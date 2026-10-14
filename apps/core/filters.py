from django_filters import rest_framework as filters

from apps.core.models import AuditLog


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    """Valeur `?champ=a,b,c` -> lookup `__in`. Utilisé pour les filtres
    "popup à cases à cocher" du frontend (ex: statut de vente, rôles d'un
    utilisateur), envoyés comme une liste de valeurs séparées par des
    virgules plutôt qu'une valeur exacte unique."""


class AuditLogFilterSet(filters.FilterSet):
    """Valeurs exactes : `entity_type=ventes.vente` ne doit pas remonter
    `ventes.venteligne` (historique d'une entité)."""

    occurred_after = filters.IsoDateTimeFilter(field_name='occurred_at', lookup_expr='gte')
    occurred_before = filters.IsoDateTimeFilter(field_name='occurred_at', lookup_expr='lte')

    class Meta:
        model = AuditLog
        fields = [
            'actor', 'entity_type', 'action', 'entity_id', 'occurred_after', 'occurred_before',
        ]
