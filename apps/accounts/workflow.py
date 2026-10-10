"""Mixin de workflow générique : une seule route `POST .../transition/{step}/`
(et `GET .../allowed-steps/`) pour n'importe quelle entité, pilotée par une
liste de règles déclarée dans l'app métier (ex. `apps.ventes.workflow.
VENTE_WORKFLOW`). Ce fichier ne connaît rien de `ventes` ni d'aucune autre
app métier — il ne lit que `step` / `permission` / `from` / `to` / `effet`.
"""

from django.db import transaction
from django.utils.module_loading import import_string
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions.has_role_permission import HasRolePermission


def find_rule(workflow, step):
    rule = next((r for r in workflow if r['step'] == step), None)
    if rule is None:
        raise NotFound(f"Étape de workflow inconnue : {step!r}.")
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


class WorkflowMixin:
    """À mélanger dans un `ModelViewSet` : définir `workflow` (la liste de
    règles) et, si `get_queryset()` ne renvoie pas toujours le modèle
    réel (ex. une vue de lecture pour `list`/`retrieve`), `workflow_model`
    explicitement."""

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
            raise PermissionDenied(f"Permission manquante : {rule['permission']}.")

        current = getattr(obj, self.status_field)
        if current not in rule['from']:
            return Response(
                {'detail': "Cette transition n'est pas autorisée depuis l'état actuel."}, status=400
            )

        with transaction.atomic():
            setattr(obj, self.status_field, rule['to'])
            obj.save(update_fields=[self.status_field, 'updated_at'])
            run_effects(rule.get('effet'), obj, request.user)

        obj.refresh_from_db()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

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
