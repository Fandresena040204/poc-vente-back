# Donne au rôle admin la permission de lire le journal d'audit
# (view_auditlog) — comme pour les autres permissions personnalisées, le
# signal post_migrate crée les permissions par défaut, mais seulement à la
# toute fin de la commande `migrate` ; on les crée ici nous-mêmes pour
# pouvoir les attribuer dans la même commande.
from django.db import migrations

from apps.core.utils import generate_reference


def seed_audit_log_permission(apps, schema_editor):
    Permission = apps.get_model('accounts', 'Permission')
    Role = apps.get_model('accounts', 'Role')

    permission, _ = Permission.objects.get_or_create(
        app_label='core',
        model='auditlog',
        codename='view_auditlog',
        defaults={'id': generate_reference('permission_id_seq', 'PRM'), 'name': 'Can view audit log'},
    )

    admin_role = Role.objects.filter(name='admin').first()
    if admin_role:
        admin_role.permissions.add(permission)


def unseed_audit_log_permission(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')

    permission = Permission.objects.filter(
        app_label='core', model='auditlog', codename='view_auditlog'
    ).first()
    if permission:
        for role in Role.objects.all():
            role.permissions.remove(permission)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
        ('accounts', '0013_userpermissionoverride'),
    ]

    operations = [
        migrations.RunPython(seed_audit_log_permission, unseed_audit_log_permission),
    ]
