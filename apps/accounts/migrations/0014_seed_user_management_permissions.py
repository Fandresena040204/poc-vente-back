# Qui peut créer un compte et attribuer des rôles : admin et dg (demandé).
# `delete_user` n'est accordé à personne — pas de suppression de compte
# prévue pour l'instant.
from django.db import migrations

ROLES = ['admin', 'dg']
CODENAMES = ['view_user', 'add_user', 'change_user']


def grant(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')

    permissions = Permission.objects.filter(
        app_label='accounts', model='user', codename__in=CODENAMES
    )
    for role in Role.objects.filter(name__in=ROLES):
        role.permissions.add(*permissions)


def revoke(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')

    permissions = Permission.objects.filter(
        app_label='accounts', model='user', codename__in=CODENAMES
    )
    for role in Role.objects.filter(name__in=ROLES):
        role.permissions.remove(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0013_userpermissionoverride'),
        ('ventes', '0017_workflow_roles_can_view_vente'),
    ]

    operations = [
        migrations.RunPython(grant, revoke),
    ]
