from django.db import migrations


class Migration(migrations.Migration):
    """Drops `auth_group`/`auth_group_permissions` — Django's built-in
    `Group` model is unused here (our own `Role`/`user_roles`/
    `role_permissions` cover RBAC instead, see [[apps/accounts/models]]).
    Kept as a normal `RunSQL` (not a fake/state-only op) so it also runs on
    a fresh `migrate` from scratch, not just on databases that already had
    these tables. Irreversible on purpose: nothing in the app ever wrote to
    these tables, so there's no data to restore.
    """

    dependencies = [
        ('accounts', '0009_rename_tables_drop_prefix'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS auth_group_permissions;
                DROP TABLE IF EXISTS auth_group;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
