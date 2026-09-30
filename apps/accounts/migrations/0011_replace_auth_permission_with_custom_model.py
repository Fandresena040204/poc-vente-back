from django.apps import apps as global_apps
from django.db import migrations, models

from apps.core.utils import generate_reference

# Liens (role_id, app_label, model, codename) capturés depuis l'ancienne
# table role_permissions (encore adossée à auth.Permission) avant qu'elle
# ne soit recréée par RemoveField/AddField ci-dessous. Portée module :
# partagé entre les deux RunPython de cette migration, exécutés dans le
# même processus, dans l'ordre de `operations`.
_captured_links = []


def _iter_permission_specs():
    # Même logique que le signal (apps/accounts/signals/permission_signals.py)
    # : utilise le vrai registre d'apps (global_apps), pas les modèles
    # historiques figés par la migration, pour bénéficier de la Meta réelle
    # des modèles (default_permissions, verbose_name...) — même rationale
    # que _ensure_permissions_exist dans 0006/0008.
    for app_config in global_apps.get_app_configs():
        if not app_config.name.startswith('apps.'):
            continue
        for model in app_config.get_models():
            if not model._meta.managed:
                continue
            for action in model._meta.default_permissions:
                yield (
                    app_config.label,
                    model._meta.model_name,
                    f'{action}_{model._meta.model_name}',
                    f'Can {action} {model._meta.verbose_name}',
                )


def create_new_permissions(apps, schema_editor):
    # apps.get_model() renvoie une version historique du modèle, sans notre
    # save() personnalisé (celui qui génère l'id via generate_reference) —
    # il faut donc générer l'id nous-mêmes ici, explicitement, uniquement
    # quand la ligne n'existe pas encore.
    Permission = apps.get_model('accounts', 'Permission')
    for app_label, model_name, codename, name in _iter_permission_specs():
        exists = Permission.objects.filter(
            app_label=app_label, model=model_name, codename=codename
        ).exists()
        if exists:
            continue
        Permission.objects.create(
            id=generate_reference('permission_id_seq', 'PRM'),
            app_label=app_label,
            model=model_name,
            codename=codename,
            name=name,
        )


def capture_role_permission_links(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    OldPermission = apps.get_model('auth', 'Permission')
    Through = Role.permissions.through

    links = []
    for role_id, permission_id in Through.objects.values_list('role_id', 'permission_id'):
        try:
            old_perm = OldPermission.objects.select_related('content_type').get(pk=permission_id)
        except OldPermission.DoesNotExist:
            continue
        links.append((role_id, old_perm.content_type.app_label, old_perm.content_type.model, old_perm.codename))

    _captured_links[:] = links


def restore_role_permission_links(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('accounts', 'Permission')
    Through = Role.permissions.through

    rows = []
    for role_id, app_label, model_name, codename in _captured_links:
        try:
            perm = Permission.objects.get(app_label=app_label, model=model_name, codename=codename)
        except Permission.DoesNotExist:
            continue
        rows.append(Through(role_id=role_id, permission_id=perm.id))

    Through.objects.bulk_create(rows, ignore_conflicts=True)
    _captured_links.clear()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_drop_unused_auth_group_tables'),
        # ventes/0005_seed_fournisseur_permissions doit avoir tourné (et créé
        # ses liens role<->permission sur l'ancien auth.Permission) avant que
        # capture_role_permission_links ci-dessous ne lise ces liens — sans
        # cette dépendance explicite (apps différentes, sinon non ordonnées
        # l'une par rapport à l'autre), le plan de migration peut placer
        # cette migration avant 0005 : les permissions fournisseur seraient
        # alors perdues (jamais capturées) et 0005 planterait en tentant
        # d'ajouter d'anciennes instances Permission à un Role.permissions
        # déjà retargeté vers le nouveau modèle.
        ('ventes', '0005_seed_fournisseur_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.CharField(editable=False, max_length=20, primary_key=True, serialize=False)),
                ('app_label', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=100)),
                ('codename', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'permission',
            },
        ),
        migrations.AddConstraint(
            model_name='permission',
            constraint=models.UniqueConstraint(
                fields=('app_label', 'model', 'codename'), name='permission_unique_codename'
            ),
        ),
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS permission_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS permission_id_seq;",
        ),
        migrations.RunPython(create_new_permissions, noop),
        migrations.RunPython(capture_role_permission_links, noop),
        migrations.RemoveField(
            model_name='role',
            name='permissions',
        ),
        migrations.AddField(
            model_name='role',
            name='permissions',
            field=models.ManyToManyField(
                blank=True, db_table='role_permissions', related_name='roles', to='accounts.permission'
            ),
        ),
        migrations.RunPython(restore_role_permission_links, noop),
    ]
