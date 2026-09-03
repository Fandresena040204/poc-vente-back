from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone

from apps.accounts.models.role import Role
from apps.accounts.models.user_manager import UserManager
from apps.core.utils import generate_reference


class User(AbstractBaseUser):
    username_validator = UnicodeUsernameValidator()

    id = models.CharField(max_length=20, primary_key=True, editable=False)
    username = models.CharField(max_length=150, unique=True, validators=[username_validator])
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    roles = models.ManyToManyField(Role, related_name='users', blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('user_id_seq', 'USR')
        super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_perms(self, perm_list, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        return self.first_name
