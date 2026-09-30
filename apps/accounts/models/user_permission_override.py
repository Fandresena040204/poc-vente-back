from django.db import models

from apps.accounts.models.permission import Permission
from apps.accounts.models.user import User


class UserPermissionOverride(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permission_overrides')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    is_allowed = models.BooleanField()

    class Meta:
        db_table = 'user_permission_override'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'permission'], name='user_permission_override_unique'
            ),
        ]

    def __str__(self):
        return f'{self.user_id} / {self.permission.codename}'
