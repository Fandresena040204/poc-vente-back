from django_filters import rest_framework as filters

from apps.core.filters import CharInFilter
from apps.ventes.models import Product


class ProductFilterSet(filters.FilterSet):
    created_at_min = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_max = filters.DateFilter(field_name='created_at', lookup_expr='lte')
    category = CharInFilter(field_name='category_id')
    is_active = filters.BooleanFilter(field_name='is_active')
    # Independent filters (not the global `search=`, which would match
    # either field and be shown as one ambiguous "name or SKU" input) —
    # each is its own toolbar filter on the frontend.
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    sku = filters.CharFilter(field_name='sku', lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['created_at_min', 'created_at_max', 'category', 'is_active', 'name', 'sku']
