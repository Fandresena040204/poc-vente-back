from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import connection, migrations


def _ensure_permissions_exist(apps):
    for app_config in global_apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None


def _next_role_id():
    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval('role_id_seq')")
        value = cursor.fetchone()[0]
    return f'ROL{value:05d}'


def seed_role_permissions(apps, schema_editor):
    _ensure_permissions_exist(apps)

    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    def get_or_create_role(name):
        role = Role.objects.filter(name=name).first()
        if role is None:
            role = Role.objects.create(id=_next_role_id(), name=name)
        return role

    def perms(app_label, model_name, actions):
        return Permission.objects.filter(
            content_type__app_label=app_label,
            content_type__model=model_name,
            codename__in=[f'{action}_{model_name}' for action in actions],
        )

    admin_role = get_or_create_role('admin')
    user_role = get_or_create_role('user')
    editor_role = get_or_create_role('editor')

    targets = [
        ('accounts', 'customer'),
        ('ventes', 'product'),
        ('ventes', 'vente'),
    ]
    for app_label, model_name in targets:
        admin_role.permissions.add(*perms(app_label, model_name, ['add', 'view', 'change', 'delete']))
        user_role.permissions.add(*perms(app_label, model_name, ['add', 'view']))
        editor_role.permissions.add(*perms(app_label, model_name, ['add', 'view', 'change']))


def unseed_role_permissions(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.filter(name__in=['user', 'editor']).delete()
    admin_role = Role.objects.filter(name='admin').first()
    if admin_role:
        admin_role.permissions.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_role_permissions'),
        ('ventes', '0002_reference_sequences'),
    ]

    operations = [
        migrations.RunPython(seed_role_permissions, unseed_role_permissions),
    ]
