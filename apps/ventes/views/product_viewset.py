from rest_framework import viewsets

from apps.accounts.permissions import HasRolePermission
from apps.ventes.filters import ProductFilterSet
from apps.ventes.models import Product, ProductListView
from apps.ventes.serializers import ProductReadSerializer, ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    # Stays `ProductSerializer` — see VenteViewSet for why (HasRolePermission
    # reads the class attribute, not get_serializer_class()).
    serializer_class = ProductSerializer
    permission_classes = [HasRolePermission]
    # No `search_fields`: `name`/`sku` are independent filters
    # (ProductFilterSet) instead of one combined global `search=`.
    ordering_fields = ['name', 'default_price', 'created_at']

    @property
    def filterset_class(self):
        # See VenteViewSet.filterset_class for why this is scoped to 'list'.
        return ProductFilterSet if self.action == 'list' else None

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ProductReadSerializer
        return ProductSerializer

    def get_queryset(self):
        # `list`/`retrieve` read from the `product_list_view` DB view
        # (category_name already resolved in SQL — see ProductListView and
        # migration 0008). `create`/`update`/`destroy` still need the real,
        # writable `Product`.
        if self.action in ('list', 'retrieve'):
            return ProductListView.objects.all()
        return Product.objects.select_related('category')
