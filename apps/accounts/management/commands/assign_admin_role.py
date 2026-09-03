from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Role
from apps.accounts.permissions import ADMIN_ROLE_NAME


class Command(BaseCommand):
    help = "Assigne le role 'admin' a un utilisateur existant."

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Utilisateur '{username}' introuvable.")

        role, _ = Role.objects.get_or_create(name=ADMIN_ROLE_NAME)
        user.roles.add(role)
        self.stdout.write(self.style.SUCCESS(f"Role 'admin' assigne a '{username}'."))
