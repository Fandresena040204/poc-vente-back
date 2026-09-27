from django.db import models


class VenteListView(models.Model):
    """Read model backed by the `ventes_vente_list_view` DB view (see
    migration 0007) — `Vente` joined with `Customer` so `customer_name` is
    resolved in SQL, once, instead of the API computing it per-request (or
    the frontend fetching every customer to resolve it itself). Read-only:
    `VenteViewSet` uses this for `list`/`retrieve` and the real `Vente`
    model for `create`/`update`/custom actions (`valider`/`annuler`).

    `status` is a plain `CharField` here (not `django_fsm.FSMField` like on
    `Vente`) — this model is never saved, so it has no need for (and
    shouldn't carry) the FSM transition machinery.
    """

    id = models.CharField(max_length=20, primary_key=True)
    customer = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=10)
    currency = models.CharField(max_length=3)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    subtotal_ht = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tva_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    expected_delivery_date = models.DateField(null=True)
    notes = models.TextField()
    created_by = models.CharField(max_length=20, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ventes_vente_list_view'
        ordering = ['-created_at']

    def __str__(self):
        return f'Vente #{self.pk} - {self.customer_name}'


class VenteLigneListView(models.Model):
    """Read model backed by `ventes_vente_ligne_list_view` — `VenteLigne`
    joined with `Product` so `product_name`/`product_sku` are resolved in
    SQL. The `vente` FK targets `VenteListView` (not the writable `Vente`)
    so `VenteListView.lines` nests correctly in `VenteReadSerializer` —
    `db_constraint=False` since there's no real FK constraint on a view
    column, this is purely for the ORM's `related_name` convenience.
    """

    id = models.CharField(max_length=20, primary_key=True)
    vente = models.ForeignKey(
        VenteListView,
        on_delete=models.DO_NOTHING,
        db_column='vente_id',
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
        db_table = 'ventes_vente_ligne_list_view'

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'
