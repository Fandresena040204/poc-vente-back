from django.db import migrations


class Migration(migrations.Migration):
    """Drops the `ventes_`/`accounts_` app-label prefix from every real table
    (`AlterModelTable` -> `ALTER TABLE ... RENAME TO ...`, non-destructive:
    data, sequences and constraints are preserved), then drops the three old
    -named views and recreates them with `CREATE OR REPLACE VIEW` (plain,
    non-materialized) under their new names, pointing at the renamed base
    tables. The `*ListView` `AlterModelTable` operations are state-only
    (Django no-ops schema changes for `managed = False` models) — they just
    keep the migration state's table name in sync with the model's
    `Meta.db_table` after this migration.
    """

    dependencies = [
        ('ventes', '0007_list_views'),
        ('accounts', '0009_rename_tables_drop_prefix'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='livraison',
            table='livraison',
        ),
        migrations.AlterModelTable(
            name='paiement',
            table='paiement',
        ),
        migrations.AlterModelTable(
            name='product',
            table='product',
        ),
        migrations.AlterModelTable(
            name='productcategory',
            table='product_category',
        ),
        migrations.AlterModelTable(
            name='vente',
            table='vente',
        ),
        migrations.AlterModelTable(
            name='venteligne',
            table='vente_ligne',
        ),
        migrations.RunSQL(
            sql="""
                DROP VIEW IF EXISTS ventes_vente_list_view;
                DROP VIEW IF EXISTS ventes_vente_ligne_list_view;
                DROP VIEW IF EXISTS ventes_product_list_view;

                CREATE OR REPLACE VIEW vente_list_view AS
                SELECT
                    v.id,
                    v.customer_id AS customer,
                    c.name AS customer_name,
                    v.status,
                    v.priority,
                    v.currency,
                    v.discount_percent,
                    v.subtotal_ht,
                    v.discount_amount,
                    v.tva_amount,
                    v.total,
                    v.expected_delivery_date,
                    v.notes,
                    v.created_by_id AS created_by,
                    v.created_at,
                    v.updated_at
                FROM vente v
                INNER JOIN customer c ON c.id = v.customer_id;

                CREATE OR REPLACE VIEW vente_ligne_list_view AS
                SELECT
                    l.id,
                    l.vente_id,
                    l.product_id AS product,
                    p.name AS product_name,
                    p.sku AS product_sku,
                    l.quantity,
                    l.unit_price,
                    l.discount_percent,
                    l.tva_rate
                FROM vente_ligne l
                INNER JOIN product p ON p.id = l.product_id;

                CREATE OR REPLACE VIEW product_list_view AS
                SELECT
                    p.id,
                    p.name,
                    p.sku,
                    p.default_price,
                    p.category_id AS category,
                    pc.name AS category_name,
                    p.description,
                    p.is_active,
                    p.created_at,
                    p.updated_at
                FROM product p
                LEFT JOIN product_category pc ON pc.id = p.category_id;
            """,
            reverse_sql="""
                DROP VIEW IF EXISTS vente_list_view;
                DROP VIEW IF EXISTS vente_ligne_list_view;
                DROP VIEW IF EXISTS product_list_view;

                CREATE OR REPLACE VIEW ventes_vente_list_view AS
                SELECT
                    v.id,
                    v.customer_id AS customer,
                    c.name AS customer_name,
                    v.status,
                    v.priority,
                    v.currency,
                    v.discount_percent,
                    v.subtotal_ht,
                    v.discount_amount,
                    v.tva_amount,
                    v.total,
                    v.expected_delivery_date,
                    v.notes,
                    v.created_by_id AS created_by,
                    v.created_at,
                    v.updated_at
                FROM vente v
                INNER JOIN customer c ON c.id = v.customer_id;

                CREATE OR REPLACE VIEW ventes_vente_ligne_list_view AS
                SELECT
                    l.id,
                    l.vente_id,
                    l.product_id AS product,
                    p.name AS product_name,
                    p.sku AS product_sku,
                    l.quantity,
                    l.unit_price,
                    l.discount_percent,
                    l.tva_rate
                FROM vente_ligne l
                INNER JOIN product p ON p.id = l.product_id;

                CREATE OR REPLACE VIEW ventes_product_list_view AS
                SELECT
                    p.id,
                    p.name,
                    p.sku,
                    p.default_price,
                    p.category_id AS category,
                    pc.name AS category_name,
                    p.description,
                    p.is_active,
                    p.created_at,
                    p.updated_at
                FROM product p
                LEFT JOIN product_category pc ON pc.id = p.category_id;
            """,
        ),
        migrations.AlterModelTable(
            name='productlistview',
            table='product_list_view',
        ),
        migrations.AlterModelTable(
            name='ventelignelistview',
            table='vente_ligne_list_view',
        ),
        migrations.AlterModelTable(
            name='ventelistview',
            table='vente_list_view',
        ),
    ]
