"""Mixin de workflow générique : une seule route `POST .../transition/{step}/`
(et `GET .../allowed-steps/`) pour n'importe quelle entité, pilotée par une
liste de règles déclarée dans l'app métier (ex. `apps.ventes.workflow.
VENTE_WORKFLOW`). Ce fichier ne connaît rien de `ventes` ni d'aucune autre
app métier — il ne lit que `step` / `permission` / `from` / `to` / `effet`.
"""

from django.db import transaction
from django.utils.module_loading import import_string
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions.has_role_permission import HasRolePermission
from apps.core.audit import log_workflow_action
from apps.core.exceptions import InvalidTransition, UnknownStep


def find_rule(workflow, step):
    rule = next((r for r in workflow if r['step'] == step), None)
    if rule is None:
        raise UnknownStep(f"Étape de workflow inconnue : « {step} ».")
    return rule


def allowed_steps(user, status, workflow, model):
    """Les étapes jouables depuis `status` par cet utilisateur — pour un
    seul objet (l'action `allowed-steps`). Dans une liste, préférer
    `allowed_steps_from_codenames` avec un jeu de codenames précalculé une
    seule fois (`HasRolePermission.effective_codenames`), pour éviter une
    requête par règle et par ligne."""
    codenames = HasRolePermission.effective_codenames(user, model)
    return allowed_steps_from_codenames(status, workflow, codenames)


def allowed_steps_from_codenames(status, workflow, codenames):
    return [
        rule['step']
        for rule in workflow
        if status in rule['from'] and rule['permission'] in codenames
    ]


def run_effects(effet, obj, user):
    if not effet:
        return
    paths = effet if isinstance(effet, (list, tuple)) else [effet]
    for path in paths:
        import_string(path)(obj, user)


# À mélanger dans un `ModelViewSet` : définir `workflow` (la liste de règles)
# et, si `get_queryset()` ne renvoie pas toujours le modèle réel (ex. une vue
# de lecture pour `list`/`retrieve`), `workflow_model` explicitement.
# Commentaire et non docstring : drf-spectacular reprend la docstring des
# classes parentes comme description de *toutes* les opérations du viewset.
class WorkflowMixin:

    workflow = None
    workflow_model = None
    status_field = 'status'

    def _workflow_model(self):
        return self.workflow_model or self.get_queryset().model

    @action(
        detail=True,
        methods=['post'],
        url_path=r'transition/(?P<step>[\w-]+)',
        permission_classes=[IsAuthenticated],
    )
    def transition(self, request, pk=None, step=None):
        obj = self.get_object()
        rule = find_rule(self.workflow, step)
        model = self._workflow_model()
        if not HasRolePermission._has_codename(request.user, model, rule['permission']):
            raise PermissionDenied(
                f"Vous n'avez pas le droit d'effectuer l'étape « {step} »."
            )

        current = getattr(obj, self.status_field)
        if current not in rule['from']:
            raise InvalidTransition()

        new_status = rule['to']
        with transaction.atomic():
            setattr(obj, self.status_field, new_status)
            obj.save(update_fields=[self.status_field, 'updated_at'])
            run_effects(rule.get('effet'), obj, request.user)
            # Entrée dédiée `workflow` avec le changement de statut dans `changes`
            # — elle se suffit à elle-même, le front n'aura pas à afficher
            # l'entrée `update` dont le seul changement est `status`.
            log_workflow_action(
                request.user, obj, step,
                changes={self.status_field: {'old': str(current), 'new': str(new_status)}},
            )

        # Renvoie l'entité telle que `retrieve` la renverrait : même
        # queryset et même serializer (donc VenteReadSerializer avec
        # allowed_steps à jour pour la vente). Le mixin reste générique :
        # il se met dans les conditions de l'action `retrieve` en
        # refetchant l'objet depuis le queryset de lecture.
        original_action = self.action
        self.action = 'retrieve'
        try:
            # Re-fetch depuis le queryset de retrieve (ex. VenteListView)
            # pour avoir les champs joints (customer_name, etc.)
            retrieve_queryset = self.get_queryset()
            obj = retrieve_queryset.get(pk=obj.pk)
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        finally:
            self.action = original_action

    @action(
        detail=True,
        methods=['get'],
        url_path='allowed-steps',
        permission_classes=[IsAuthenticated],
    )
    def list_allowed_steps(self, request, pk=None):
        obj = self.get_object()
        current = getattr(obj, self.status_field)
        steps = allowed_steps(request.user, current, self.workflow, self._workflow_model())
        return Response({'allowed_steps': steps})
