from rest_framework.permissions import BasePermission

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
        codename = f'{action}_{model._meta.model_name}'

        return user.roles.filter(
            permissions__codename=codename,
            permissions__content_type__app_label=model._meta.app_label,
        ).exists()
