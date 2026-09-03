from django.db import models

from apps.core.utils import generate_reference
from apps.ventes.models.product import Product
from apps.ventes.models.vente import Vente


class VenteLigne(models.Model):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='+')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('vente_ligne_id_seq', 'LGN')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.quantity} x {self.product}'
