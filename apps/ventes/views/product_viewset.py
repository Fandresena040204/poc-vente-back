from rest_framework import viewsets

from apps.accounts.permissions import HasRolePermission
from apps.ventes.models import Product
from apps.ventes.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [HasRolePermission]
    search_fields = ['name', 'sku']
    ordering_fields = ['name', 'default_price']
