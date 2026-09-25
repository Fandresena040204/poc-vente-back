from rest_framework import viewsets

from apps.accounts.filters import CustomerFilterSet
from apps.accounts.models import Customer
from apps.accounts.permissions import HasRolePermission
from apps.accounts.serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [HasRolePermission]
    filterset_class = CustomerFilterSet
    search_fields = ['name', 'email', 'city']
    ordering_fields = ['name', 'created_at', 'birth_date']
