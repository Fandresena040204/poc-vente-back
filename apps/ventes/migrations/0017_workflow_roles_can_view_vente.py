# achat/caisse/dg n'avaient que les permissions de workflow
# (validate_*/reject_*/cancel_vente) : sans `view_vente`, impossible de
# charger une vente pour agir dessus (list/retrieve exigent `view`, voir
# HasRolePermission.ACTION_TO_PERMISSION) — découvert en testant le
# parcours dans le navigateur avec ces rôles.
from django.db import migrations

ROLES = ['achat', 'caisse', 'dg']


def grant_view_vente(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')

    permission = Permission.objects.get(app_label='ventes', model='vente', codename='view_vente')
    for role in Role.objects.filter(name__in=ROLES):
        role.permissions.add(permission)


def revoke_view_vente(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')

    permission = Permission.objects.filter(
        app_label='ventes', model='vente', codename='view_vente'
    ).first()
    if permission:
        for role in Role.objects.filter(name__in=ROLES):
            role.permissions.remove(permission)


class Migration(migrations.Migration):
    dependencies = [
        ('ventes', '0016_seed_vente_workflow_permissions'),
    ]

    operations = [
        migrations.RunPython(grant_view_vente, revoke_view_vente),
    ]
