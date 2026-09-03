from rest_framework import viewsets

from apps.accounts.models import Customer
from apps.accounts.permissions import HasRolePermission
from apps.accounts.serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [HasRolePermission]
    search_fields = ['name', 'email']
    ordering_fields = ['name', 'created_at']
