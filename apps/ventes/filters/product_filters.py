from django_filters import rest_framework as filters

from apps.ventes.models import Product


class ProductFilterSet(filters.FilterSet):
    created_at_min = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_max = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['created_at_min', 'created_at_max']
