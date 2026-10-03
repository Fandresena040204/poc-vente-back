from django_filters import rest_framework as filters

from apps.core.filters import CharInFilter
from apps.ventes.models import ProductListView


class ProductFilterSet(filters.FilterSet):
    # Targets `ProductListView` (the DB view) — see VenteFilterSet for why.
    # `category` is a plain CharField on the view (not a ForeignKey like on
    # `Product`), hence `field_name='category'` rather than `'category_id'`.
    created_at_min = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_max = filters.DateFilter(field_name='created_at', lookup_expr='lte')
    category = CharInFilter(field_name='category')
    is_active = filters.BooleanFilter(field_name='is_active')
    # Independent filters (not the global `search=`, which would match
    # either field and be shown as one ambiguous "name or SKU" input) —
    # each is its own toolbar filter on the frontend.
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    sku = filters.CharFilter(field_name='sku', lookup_expr='icontains')

    class Meta:
        model = ProductListView
        fields = ['created_at_min', 'created_at_max', 'category', 'is_active', 'name', 'sku']
