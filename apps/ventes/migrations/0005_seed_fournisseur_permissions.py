from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations


def _ensure_permissions_exist(apps):
    for app_config in global_apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None


def seed_fournisseur_permissions(apps, schema_editor):
    _ensure_permissions_exist(apps)

    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    def perms(actions):
        return Permission.objects.filter(
            content_type__app_label='ventes',
            content_type__model='fournisseur',
            codename__in=[f'{action}_fournisseur' for action in actions],
        )

    admin_role = Role.objects.filter(name='admin').first()
    user_role = Role.objects.filter(name='user').first()
    editor_role = Role.objects.filter(name='editor').first()

    if admin_role:
        admin_role.permissions.add(*perms(['add', 'view', 'change', 'delete']))
    if user_role:
        user_role.permissions.add(*perms(['add', 'view']))
    if editor_role:
        editor_role.permissions.add(*perms(['add', 'view', 'change']))


def unseed_fournisseur_permissions(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('auth', 'Permission')
    fournisseur_perms = Permission.objects.filter(
        content_type__app_label='ventes', content_type__model='fournisseur'
    )
    for role in Role.objects.all():
        role.permissions.remove(*fournisseur_perms)


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0004_fournisseur'),
        ('accounts', '0006_seed_role_permissions'),
    ]

    operations = [
        migrations.RunPython(seed_fournisseur_permissions, unseed_fournisseur_permissions),
    ]
