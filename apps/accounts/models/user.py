from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.models.role import Role
from apps.core.utils import generate_reference


class User(AbstractUser):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    roles = models.ManyToManyField(Role, related_name='users', blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('user_id_seq', 'USR')
        super().save(*args, **kwargs)
