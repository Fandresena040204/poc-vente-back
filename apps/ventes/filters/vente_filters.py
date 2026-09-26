from django_filters import rest_framework as filters

from apps.core.filters import CharInFilter
from apps.ventes.models import Vente


class VenteFilterSet(filters.FilterSet):
    status = CharInFilter(field_name='status')
    priority = CharInFilter(field_name='priority')
    currency = CharInFilter(field_name='currency')
    # Explicit CharInFilter (comma-separated ids) instead of the default
    # exact-match FK filter Meta.fields would generate — consistent with
    # status/priority/currency, and matches the frontend's checkbox-style
    # faceted filter (multi-select) rather than a single value.
    customer = CharInFilter(field_name='customer')
    total_min = filters.NumberFilter(field_name='total', lookup_expr='gte')
    total_max = filters.NumberFilter(field_name='total', lookup_expr='lte')
    expected_delivery_date_min = filters.DateFilter(
        field_name='expected_delivery_date', lookup_expr='gte'
    )
    expected_delivery_date_max = filters.DateFilter(
        field_name='expected_delivery_date', lookup_expr='lte'
    )

    class Meta:
        model = Vente
        fields = [
            'status', 'priority', 'currency', 'customer', 'total_min', 'total_max',
            'expected_delivery_date_min', 'expected_delivery_date_max',
        ]
