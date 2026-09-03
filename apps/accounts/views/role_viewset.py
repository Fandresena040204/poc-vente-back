from django.contrib.auth.models import Group
from rest_framework import permissions, viewsets

from apps.accounts.serializers import RoleSerializer


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    queryset = Group.objects.all()
    permission_classes = [permissions.IsAdminUser]
