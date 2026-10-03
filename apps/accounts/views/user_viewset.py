from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.filters import UserFilterSet
from apps.accounts.models import Permission, Role, UserPermissionOverride
from apps.accounts.permissions import IsAdminRole
from apps.accounts.serializers import UserListSerializer, UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserListSerializer
    permission_classes = [IsAdminRole]
    filterset_class = UserFilterSet
    # No `search_fields`: `username` is its own filter (UserFilterSet)
    # rather than the global `search=`.
    ordering_fields = ['username', 'date_joined']

    def get_queryset(self):
        # .distinct() nécessaire : le filtre `roles` (UserFilterSet) traverse
        # la relation M2M roles, qui peut dupliquer les lignes utilisateur.
        return User.objects.all().prefetch_related('roles').distinct()

    def get_serializer_class(self):
        # Le document (§5) ne prévoit `permission_overrides` que dans la
        # réponse des actions set/clear — mais le dialog de la matrice (§8)
        # doit aussi pouvoir lire l'état initial des overrides d'un user
        # avant le premier clic. `retrieve` (GET /api/users/{id}/) bascule
        # donc sur UserSerializer (permissions + permission_overrides
        # inclus) ; `list` garde UserListSerializer, inchangé.
        if self.action == 'retrieve':
            return UserSerializer
        return super().get_serializer_class()

    def _set_role(self, request, pk, action_name):
        user = self.get_object()
        role_name = request.data.get('role')
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            return Response(
                {'detail': f"Role '{role_name}' introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        getattr(user.roles, action_name)(role)
        return Response(UserListSerializer(user).data)

    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        return self._set_role(request, pk, 'add')

    @action(detail=True, methods=['post'])
    def remove_role(self, request, pk=None):
        return self._set_role(request, pk, 'remove')

    @action(detail=True, methods=['post'])
    def set_permission_override(self, request, pk=None):
        user = self.get_object()
        permission = get_object_or_404(Permission, codename=request.data['permission'])
        UserPermissionOverride.objects.update_or_create(
            user=user,
            permission=permission,
            defaults={'is_allowed': request.data['is_allowed']},
        )
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=['post'])
    def clear_permission_override(self, request, pk=None):
        user = self.get_object()
        permission = get_object_or_404(Permission, codename=request.data['permission'])
        UserPermissionOverride.objects.filter(user=user, permission=permission).delete()
        return Response(UserSerializer(user).data)
