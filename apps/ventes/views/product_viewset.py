from rest_framework import viewsets

from apps.accounts.permissions import HasRolePermission
from apps.ventes.filters import ProductFilterSet
from apps.ventes.models import Product
from apps.ventes.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [HasRolePermission]
    filterset_class = ProductFilterSet
    # No `search_fields`: `name`/`sku` are independent filters
    # (ProductFilterSet) instead of one combined global `search=`.
    ordering_fields = ['name', 'default_price', 'created_at']

    def get_queryset(self):
        return Product.objects.select_related('category')
