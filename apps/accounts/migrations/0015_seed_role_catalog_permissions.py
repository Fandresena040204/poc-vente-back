# RoleViewSet est passé de IsAdminRole (bypass total) à HasRolePermission
# (apps/accounts/views/role_viewset.py) : sans cette migration, plus
# personne — même admin — n'aurait accès à /api/roles/. Admin garde la
# gestion complète du catalogue des rôles ; dg ne peut que les lister
# (nécessaire pour attribuer un rôle existant à un utilisateur, voir
# accounts/0014_seed_user_management_permissions.py), pas en créer/modifier.
from django.db import migrations

ADMIN_CODENAMES = ['view_role', 'add_role', 'change_role', 'delete_role']
DG_CODENAMES = ['view_role']


def grant(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')

    def perms(codenames):
        return Permission.objects.filter(app_label='accounts', model='role', codename__in=codenames)

    admin_role = Role.objects.filter(name='admin').first()
    if admin_role:
        admin_role.permissions.add(*perms(ADMIN_CODENAMES))

    dg_role = Role.objects.filter(name='dg').first()
    if dg_role:
        dg_role.permissions.add(*perms(DG_CODENAMES))


def revoke(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')

    role_perms = Permission.objects.filter(app_label='accounts', model='role')
    for role in Role.objects.filter(name__in=['admin', 'dg']):
        role.permissions.remove(*role_perms)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0014_seed_user_management_permissions'),
    ]

    operations = [
        migrations.RunPython(grant, revoke),
    ]
