from django_filters import rest_framework as filters

from apps.ventes.models import ProductCategory


class ProductCategoryFilterSet(filters.FilterSet):
    class Meta:
        model = ProductCategory
        fields: list[str] = []
