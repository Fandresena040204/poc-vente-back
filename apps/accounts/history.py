"""Historique par entité : une route `GET .../{pk}/history/` pour n'importe
quel viewset, lue dans le journal d'audit général (`apps.core.models.
AuditLog`). Ne connaît rien de `ventes` ni d'aucune autre app métier.

Soumise à `view_<modèle>` et non à `view_auditlog` : qui peut voir l'entité
peut voir son historique, sans pour autant lire tout le journal (connexions
des autres utilisateurs, autres entités).
"""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions.has_role_permission import HasRolePermission
from apps.core.models import AuditLog
from apps.core.serializers import AuditLogSerializer


# À mélanger dans un `ModelViewSet`. Le modèle réel est `history_model`, sinon
# `workflow_model` (`WorkflowMixin`), sinon `get_queryset().model`.
# Commentaire et non docstring : voir `WorkflowMixin`.
class HistoryMixin:
    history_model = None

    def _history_model(self):
        return (
            self.history_model
            or getattr(self, 'workflow_model', None)
            or self.get_queryset().model
        )

    # `many=True` : drf-spectacular documente la vraie réponse paginée.
    @extend_schema(
        responses=AuditLogSerializer(many=True),
        description="Historique de l'entité, du plus récent au plus ancien.",
    )
    @action(detail=True, methods=['get'], url_path='history', permission_classes=[IsAuthenticated])
    def history(self, request, pk=None):
        obj = self.get_object()
        model = self._history_model()
        codename = f'view_{model._meta.model_name}'
        if not HasRolePermission._has_codename(request.user, model, codename):
            raise PermissionDenied("Vous n'avez pas la permission de voir cet historique.")

        entries = AuditLog.objects.filter(
            entity_type=f'{model._meta.app_label}.{model._meta.model_name}',
            entity_id=str(obj.pk),
        # `-id` départage les entrées d'une même étape (même horodatage).
        ).order_by('-occurred_at', '-id')
        page = self.paginate_queryset(entries)
        return self.get_paginated_response(AuditLogSerializer(page, many=True).data)
