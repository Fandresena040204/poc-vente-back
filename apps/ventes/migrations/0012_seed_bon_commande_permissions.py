from django.contrib.auth.management import create_permissions
from django.db import migrations


def _ensure_permissions_exist(apps):
    from django.apps import apps as global_apps

    for app_config in global_apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None


def seed_bon_commande_permissions(apps, schema_editor):
    _ensure_permissions_exist(apps)

    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    def perms(actions):
        return Permission.objects.filter(
            content_type__app_label='ventes',
            content_type__model='boncommande',
            codename__in=[f'{action}_boncommande' for action in actions],
        )

    admin_role = Role.objects.filter(name='admin').first()
    editor_role = Role.objects.filter(name='editor').first()
    user_role = Role.objects.filter(name='user').first()

    if admin_role:
        admin_role.permissions.add(*perms(['add', 'view', 'change', 'delete']))
    if editor_role:
        editor_role.permissions.add(*perms(['add', 'view', 'change']))
    if user_role:
        user_role.permissions.add(*perms(['add', 'view']))


def unseed_bon_commande_permissions(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    bon_commande_perms = Permission.objects.filter(
        content_type__app_label='ventes',
        content_type__model='boncommande',
    )
    for role in Role.objects.all():
        role.permissions.remove(*bon_commande_perms)


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0011_boncommande_boncommandeligne'),
        ('accounts', '0010_drop_unused_auth_group_tables'),
    ]

    operations = [
        migrations.RunPython(seed_bon_commande_permissions, unseed_bon_commande_permissions),
    ]
