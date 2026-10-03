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
    date_joined = models.DateTimeField(default=timezone.now)

    roles = models.ManyToManyField(Role, related_name='users', blank=True, db_table='user_roles')

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'user'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('user_id_seq', 'USR')
        super().save(*args, **kwargs)

    @property
    def is_staff(self):
        # Pas un vrai champ : l'admin Django n'est plus utilisé pour gérer
        # quoi que ce soit côté accounts (§0.1) — cette propriété évite
        # juste un AttributeError dans AdminSite.has_permission (qui lit
        # request.user.is_staff en interne), pour que /admin/ refuse
        # proprement l'accès plutôt que de planter en 500.
        return False

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        return self.first_name
