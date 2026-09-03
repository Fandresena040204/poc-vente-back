from rest_framework import permissions, viewsets

from apps.accounts.models import Role
from apps.accounts.serializers import RoleSerializer


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    permission_classes = [permissions.IsAdminUser]
