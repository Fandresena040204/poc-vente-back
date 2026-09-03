from django.db import models

from apps.ventes.models.product import Product
from apps.ventes.models.vente import Vente


class VenteLigne(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='+')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.product}'
