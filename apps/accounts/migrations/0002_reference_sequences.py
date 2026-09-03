from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS customer_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS customer_id_seq;",
        ),
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS role_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS role_id_seq;",
        ),
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS user_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS user_id_seq;",
        ),
    ]
