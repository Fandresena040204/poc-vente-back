import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Adds three read-only DB views (Vente/VenteLigne/Product joined with
    the entity whose id they store, to resolve a `*_name` label in SQL) and
    the unmanaged Django models mapped to them. `CreateModel` for a
    `managed = False` model is state-only (Django's schema editor no-ops
    table creation for unmanaged models) — the `RunSQL` operations below do
    the actual `CREATE VIEW` work.
    """

    dependencies = [
        ('ventes', '0006_vente_currency_vente_discount_amount_and_more'),
        ('accounts', '0008_seed_more_role_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductListView',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('sku', models.CharField(max_length=64)),
                ('default_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('category', models.CharField(max_length=20, null=True)),
                ('category_name', models.CharField(max_length=100, null=True)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField()),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField()),
            ],
            options={
                'db_table': 'ventes_product_list_view',
                'ordering': ['name'],
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VenteListView',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('customer', models.CharField(max_length=20)),
                ('customer_name', models.CharField(max_length=255)),
                ('status', models.CharField(max_length=50)),
                ('priority', models.CharField(max_length=10)),
                ('currency', models.CharField(max_length=3)),
                ('discount_percent', models.DecimalField(decimal_places=2, max_digits=5)),
                ('subtotal_ht', models.DecimalField(decimal_places=2, max_digits=12)),
                ('discount_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('tva_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('expected_delivery_date', models.DateField(null=True)),
                ('notes', models.TextField()),
                ('created_by', models.CharField(max_length=20, null=True)),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField()),
            ],
            options={
                'db_table': 'ventes_vente_list_view',
                'ordering': ['-created_at'],
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VenteLigneListView',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('product', models.CharField(max_length=20)),
                ('product_name', models.CharField(max_length=255)),
                ('product_sku', models.CharField(max_length=64)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_percent', models.DecimalField(decimal_places=2, max_digits=5)),
                ('tva_rate', models.DecimalField(decimal_places=2, max_digits=5)),
                (
                    'vente',
                    models.ForeignKey(
                        db_column='vente_id',
                        db_constraint=False,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='lines',
                        to='ventes.ventelistview',
                    ),
                ),
            ],
            options={
                'db_table': 'ventes_vente_ligne_list_view',
                'managed': False,
            },
        ),
        migrations.RunSQL(
            sql="""
                CREATE VIEW ventes_vente_list_view AS
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
                FROM ventes_vente v
                INNER JOIN accounts_customer c ON c.id = v.customer_id;
            """,
            reverse_sql="DROP VIEW IF EXISTS ventes_vente_list_view;",
        ),
        migrations.RunSQL(
            sql="""
                CREATE VIEW ventes_vente_ligne_list_view AS
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
                FROM ventes_venteligne l
                INNER JOIN ventes_product p ON p.id = l.product_id;
            """,
            reverse_sql="DROP VIEW IF EXISTS ventes_vente_ligne_list_view;",
        ),
        migrations.RunSQL(
            sql="""
                CREATE VIEW ventes_product_list_view AS
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
                FROM ventes_product p
                LEFT JOIN ventes_productcategory pc ON pc.id = p.category_id;
            """,
            reverse_sql="DROP VIEW IF EXISTS ventes_product_list_view;",
        ),
    ]
