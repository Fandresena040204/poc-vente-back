from rest_framework import viewsets

from apps.accounts.filters import RoleFilterSet
from apps.accounts.models import Role
from apps.accounts.permissions import HasRolePermission
from apps.accounts.serializers import RoleSerializer


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    # `HasRolePermission`, pas `IsAdminRole` : attribuer un rôle existant à
    # un utilisateur (users-create-page.tsx, users-roles-page.tsx) a besoin
    # de lire la liste des rôles (`view_role`) — admin et dg l'ont (voir la
    # migration de seed) ; gérer le catalogue des rôles lui-même
    # (add/change/delete_role) reste admin seulement.
    permission_classes = [HasRolePermission]
    filterset_class = RoleFilterSet
    # No `search_fields`: `name` is its own filter (RoleFilterSet) rather
    # than the global `search=`.
    ordering_fields = ['name']
