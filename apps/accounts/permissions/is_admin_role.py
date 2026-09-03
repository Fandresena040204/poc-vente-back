from rest_framework.permissions import BasePermission

ADMIN_ROLE_NAME = 'admin'


class IsAdminRole(BasePermission):
    message = "Necessite le role 'admin'."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        return user.roles.filter(name=ADMIN_ROLE_NAME).exists()
