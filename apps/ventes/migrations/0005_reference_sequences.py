from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0004_productcategory_product_description_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS product_category_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS product_category_id_seq;",
        ),
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS livraison_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS livraison_id_seq;",
        ),
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS paiement_id_seq;",
            reverse_sql="DROP SEQUENCE IF EXISTS paiement_id_seq;",
        ),
    ]
