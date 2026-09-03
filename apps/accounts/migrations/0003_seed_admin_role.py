from django.db import connection, migrations


def create_admin_role(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    if Role.objects.filter(name='admin').exists():
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval('role_id_seq')")
        next_value = cursor.fetchone()[0]
    Role.objects.create(id=f'ROL{next_value:05d}', name='admin')


def remove_admin_role(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.filter(name='admin').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_reference_sequences'),
    ]

    operations = [
        migrations.RunPython(create_admin_role, remove_admin_role),
    ]
