from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS product_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS product_id_seq;",
        ),
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS vente_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS vente_id_seq;",
        ),
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS vente_ligne_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS vente_ligne_id_seq;",
        ),
    ]
