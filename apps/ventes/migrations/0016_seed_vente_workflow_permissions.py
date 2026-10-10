# Crée les permissions de VENTE_WORKFLOW (apps/ventes/workflow.py) si le
# signal post_migrate ne l'a pas encore fait (il ne tourne qu'à la toute
# fin d'une commande `migrate`, après cette migration), et les attache aux
# rôles. Achat et caisse valident/rejettent tous les deux l'étape achat
# ("achat doit aussi valider" + caisse peut sauter l'achat) ; dg la sienne ;
# admin garde tout. cancel_vente (brouillon) est ouvert à toute la chaîne.
from django.db import migrations

from apps.core.utils import generate_reference
from apps.ventes.workflow import VENTE_WORKFLOW

ROLE_GRANTS = {
    'admin': [rule['permission'] for rule in VENTE_WORKFLOW],
    'achat': ['validate_achat_vente', 'reject_achat_vente', 'cancel_vente'],
    'caisse': [
        'validate_achat_vente', 'reject_achat_vente',
        'validate_caisse_vente', 'reject_caisse_vente',
        'cancel_vente',
    ],
    'dg': ['validate_dg_vente', 'reject_dg_vente', 'cancel_vente'],
}


def _ensure_permissions_exist(apps):
    Permission = apps.get_model('accounts', 'Permission')
    for rule in VENTE_WORKFLOW:
        Permission.objects.get_or_create(
            app_label='ventes',
            model='vente',
            codename=rule['permission'],
            defaults={'id': generate_reference('permission_id_seq', 'PRM'), 'name': rule['step']},
        )


def seed_vente_workflow_permissions(apps, schema_editor):
    _ensure_permissions_exist(apps)

    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')

    def perms(codenames):
        return Permission.objects.filter(app_label='ventes', model='vente', codename__in=codenames)

    for role_name, codenames in ROLE_GRANTS.items():
        role, _ = Role.objects.get_or_create(
            name=role_name, defaults={'id': generate_reference('role_id_seq', 'ROL')}
        )
        role.permissions.add(*perms(codenames))


def unseed_vente_workflow_permissions(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')

    all_codenames = [rule['permission'] for rule in VENTE_WORKFLOW]
    workflow_perms = Permission.objects.filter(
        app_label='ventes', model='vente', codename__in=all_codenames
    )
    for role in Role.objects.filter(name__in=ROLE_GRANTS.keys()):
        role.permissions.remove(*workflow_perms)


class Migration(migrations.Migration):
    dependencies = [
        ('ventes', '0015_vente_workflow'),
    ]

    operations = [
        migrations.RunPython(seed_vente_workflow_permissions, unseed_vente_workflow_permissions),
    ]
