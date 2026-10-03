from rest_framework import viewsets

from apps.accounts.filters import RoleFilterSet
from apps.accounts.models import Role
from apps.accounts.permissions import IsAdminRole
from apps.accounts.serializers import RoleSerializer


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    permission_classes = [IsAdminRole]
    filterset_class = RoleFilterSet
    # No `search_fields`: `name` is its own filter (RoleFilterSet) rather
    # than the global `search=`.
    ordering_fields = ['name']
