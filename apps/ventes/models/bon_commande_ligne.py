from django.db import models

from apps.core.utils import generate_reference
from apps.ventes.models.bon_commande import BonCommande
from apps.ventes.models.product import Product


class BonCommandeLigne(models.Model):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    bon_commande = models.ForeignKey(BonCommande, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='+')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tva_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20)

    class Meta:
        db_table = 'bon_commande_ligne'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('bon_commande_ligne_id_seq', 'BCL')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.quantity} x {self.product}'
