from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations


def _ensure_permissions_exist(apps):
    for app_config in global_apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None


def seed_more_role_permissions(apps, schema_editor):
    """Same as accounts/0006_seed_role_permissions.py, extended to the
    models added on top of the initial schema (Product.category,
    Livraison, Paiement) — otherwise `HasRolePermission` 403s every
    request against these new endpoints for every non-superuser role."""
    _ensure_permissions_exist(apps)

    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    def perms(app_label, model_name, actions):
        return Permission.objects.filter(
            content_type__app_label=app_label,
            content_type__model=model_name,
            codename__in=[f'{action}_{model_name}' for action in actions],
        )

    admin_role = Role.objects.filter(name='admin').first()
    user_role = Role.objects.filter(name='user').first()
    editor_role = Role.objects.filter(name='editor').first()

    targets = [
        ('ventes', 'productcategory'),
        ('ventes', 'livraison'),
        ('ventes', 'paiement'),
    ]
    for app_label, model_name in targets:
        if admin_role:
            admin_role.permissions.add(*perms(app_label, model_name, ['add', 'view', 'change', 'delete']))
        if user_role:
            user_role.permissions.add(*perms(app_label, model_name, ['add', 'view']))
        if editor_role:
            editor_role.permissions.add(*perms(app_label, model_name, ['add', 'view', 'change']))


def unseed_more_role_permissions(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    targets = [
        ('ventes', 'productcategory'),
        ('ventes', 'livraison'),
        ('ventes', 'paiement'),
    ]
    for role in Role.objects.filter(name__in=['admin', 'user', 'editor']):
        for app_label, model_name in targets:
            role.permissions.remove(
                *Permission.objects.filter(
                    content_type__app_label=app_label, content_type__model=model_name
                )
            )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_customer_address_customer_birth_date_customer_city_and_more'),
        ('ventes', '0005_reference_sequences'),
    ]

    operations = [
        migrations.RunPython(seed_more_role_permissions, unseed_more_role_permissions),
    ]
