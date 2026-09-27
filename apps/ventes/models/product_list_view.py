from django.db import models


class ProductListView(models.Model):
    """Read model backed by the `ventes_product_list_view` DB view (see
    migration 0007) — `Product` joined with `ProductCategory` so
    `category_name` is resolved in SQL, once, instead of the API computing
    it per-request (or the frontend fetching every category to resolve it
    itself). Read-only: `ProductViewSet` uses this for `list`/`retrieve`
    and the real `Product` model for `create`/`update`/`destroy`.
    """

    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64)
    default_price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, null=True)
    category_name = models.CharField(max_length=100, null=True)
    description = models.TextField()
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ventes_product_list_view'
        ordering = ['name']

    def __str__(self):
        return self.name
