from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.serializers import UserListSerializer

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserListSerializer
    queryset = User.objects.all().prefetch_related('groups')
    permission_classes = [permissions.IsAdminUser]

    def _set_role(self, request, pk, action_name):
        user = self.get_object()
        role_name = request.data.get('role')
        try:
            group = Group.objects.get(name=role_name)
        except Group.DoesNotExist:
            return Response(
                {'detail': f"Role '{role_name}' introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        getattr(user.groups, action_name)(group)
        return Response(UserListSerializer(user).data)

    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        return self._set_role(request, pk, 'add')

    @action(detail=True, methods=['post'])
    def remove_role(self, request, pk=None):
        return self._set_role(request, pk, 'remove')
