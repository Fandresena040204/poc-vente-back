from rest_framework.permissions import BasePermission

from apps.accounts.models import UserPermissionOverride

ACTION_TO_PERMISSION = {
    'list': 'view',
    'retrieve': 'view',
    'create': 'add',
    'update': 'change',
    'partial_update': 'change',
    'destroy': 'delete',
}


class HasRolePermission(BasePermission):
    message = "Aucun de vos roles ne dispose de la permission requise."
    default_custom_action_permission = 'change'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        action = ACTION_TO_PERMISSION.get(view.action, self.default_custom_action_permission)
        model = view.serializer_class.Meta.model
        if not self._has_codename(user, model, action):
            return False
        # A write must also be readable: without `view`, a change would still
        # succeed on an entity the user is not allowed to see.
        return action == 'view' or self._has_codename(user, model, 'view')

    @staticmethod
    def _has_codename(user, model, action):
        codename = f'{action}_{model._meta.model_name}'

        override = UserPermissionOverride.objects.filter(
            user=user,
            permission__codename=codename,
            permission__app_label=model._meta.app_label,
        ).first()
        if override is not None:
            return override.is_allowed

        return user.roles.filter(
            permissions__codename=codename,
            permissions__app_label=model._meta.app_label,
        ).exists()
