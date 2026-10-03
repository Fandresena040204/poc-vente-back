from django.db import models

from apps.accounts.models import Customer
from apps.core.models import AuditedModel
from apps.core.utils import generate_reference
from apps.ventes.models.vente import VenteCurrency


class BonCommande(AuditedModel):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='bons_commande')
    currency = models.CharField(
        max_length=3, choices=VenteCurrency.choices, default=VenteCurrency.MGA
    )
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    expected_delivery_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'bon_commande'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('bon_commande_id_seq', 'BDC')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'BonCommande #{self.pk} - {self.customer}'
