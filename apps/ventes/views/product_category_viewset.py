from rest_framework import viewsets

from apps.accounts.permissions import HasRolePermission
from apps.ventes.filters import ProductCategoryFilterSet
from apps.ventes.models import ProductCategory
from apps.ventes.serializers import ProductCategorySerializer


class ProductCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all()
    permission_classes = [HasRolePermission]
    filterset_class = ProductCategoryFilterSet
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
