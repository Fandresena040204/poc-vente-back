from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_replace_auth_permission_with_custom_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_staff',
        ),
    ]
