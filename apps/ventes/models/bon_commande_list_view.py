from django.db import models


class BonCommandeListView(models.Model):
    """Read model backed by the `bon_commande_list_view` DB view — `BonCommande`
    joined with `Customer` so `customer_name` is resolved in SQL. Read-only:
    `BonCommandeViewSet` uses it for `list`/`retrieve`, the real model for
    writes and `to_vente_defaults`.
    """

    id = models.CharField(max_length=20, primary_key=True)
    customer = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=255)
    currency = models.CharField(max_length=3)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    expected_delivery_date = models.DateField(null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'bon_commande_list_view'
        ordering = ['-created_at']

    def __str__(self):
        return f'BonCommande #{self.pk} - {self.customer_name}'


class BonCommandeLigneListView(models.Model):
    """Read model backed by `bon_commande_ligne_list_view` — lines joined with
    `Product` so `product_name`/`product_sku` are resolved in SQL. The FK
    targets `BonCommandeListView` so `lines` nests in the read serializer.
    """

    id = models.CharField(max_length=20, primary_key=True)
    bon_commande = models.ForeignKey(
        BonCommandeListView,
        on_delete=models.DO_NOTHING,
        db_column='bon_commande_id',
        db_constraint=False,
        related_name='lines',
    )
    product = models.CharField(max_length=20)
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=64)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    tva_rate = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'bon_commande_ligne_list_view'

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'
