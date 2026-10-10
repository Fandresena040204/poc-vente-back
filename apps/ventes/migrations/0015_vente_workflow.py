# Vente.status : texte ('draft'/'validated'/'cancelled') -> entier (voir
# apps/ventes/workflow.py:VenteStatus). La conversion de données se fait
# dans le même `USING` que le changement de type de colonne (une vue dépend
# de la colonne, donc on la supprime et on la recrée dans le même bloc SQL,
# plutôt qu'en opérations séparées — garde l'ordre correct à l'aller comme
# au retour).
from django.db import migrations, models


VIEW_SQL = """
    CREATE VIEW vente_list_view AS
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
"""


class Migration(migrations.Migration):
    dependencies = [
        ('ventes', '0014_bon_commande_ligne_list_view_view'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='vente',
            options={
                'ordering': ['-created_at'],
                'permissions': [
                    ('validate_achat_vente', 'valider_achat'),
                    ('reject_achat_vente', 'rejeter_achat'),
                    ('validate_caisse_vente', 'valider_caisse'),
                    ('reject_caisse_vente', 'rejeter_caisse'),
                    ('validate_dg_vente', 'valider_dg'),
                    ('reject_dg_vente', 'rejeter_dg'),
                    ('cancel_vente', 'annuler'),
                ],
            },
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=f"""
                        DROP VIEW IF EXISTS vente_list_view;
                        ALTER TABLE vente ALTER COLUMN status DROP DEFAULT;
                        ALTER TABLE vente ALTER COLUMN status TYPE integer USING (
                            CASE status
                                WHEN 'draft' THEN 1
                                WHEN 'validated' THEN 9
                                WHEN 'cancelled' THEN -1
                                ELSE 1
                            END
                        );
                        ALTER TABLE vente ALTER COLUMN status SET DEFAULT 1;
                        {VIEW_SQL}
                    """,
                    reverse_sql=f"""
                        DROP VIEW IF EXISTS vente_list_view;
                        ALTER TABLE vente ALTER COLUMN status DROP DEFAULT;
                        ALTER TABLE vente ALTER COLUMN status TYPE varchar(50) USING (
                            CASE status
                                WHEN 1 THEN 'draft'
                                WHEN 9 THEN 'validated'
                                WHEN -1 THEN 'cancelled'
                                ELSE 'draft'
                            END
                        );
                        ALTER TABLE vente ALTER COLUMN status SET DEFAULT 'draft';
                        {VIEW_SQL}
                    """,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='vente',
                    name='status',
                    field=models.IntegerField(
                        choices=[
                            (1, 'Brouillon'),
                            (3, 'Validée (achat)'),
                            (6, 'Validée (caisse)'),
                            (9, 'Validée (DG)'),
                            (-1, 'Annulée'),
                            (-3, 'Rejetée (achat)'),
                            (-6, 'Rejetée (caisse)'),
                            (-9, 'Rejetée (DG)'),
                        ],
                        default=1,
                    ),
                ),
            ],
        ),
    ]
