from decimal import Decimal

from django.db import models

from apps.accounts.models import Customer
from apps.core.models import AuditedModel


class VenteStatus(models.TextChoices):
    DRAFT = 'draft', 'Brouillon'
    VALIDATED = 'validated', 'Validée'
    CANCELLED = 'cancelled', 'Annulée'


class Vente(AuditedModel):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='ventes')
    status = models.CharField(max_length=20, choices=VenteStatus.choices, default=VenteStatus.DRAFT)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Vente #{self.pk} - {self.customer}'

    def recalculate_total(self):
        total = self.lines.aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_price'))
        )['total'] or Decimal('0')
        self.total = total
        self.save(update_fields=['total', 'updated_at'])

    def validate_vente(self):
        if self.status != VenteStatus.DRAFT:
            raise ValueError("Seule une vente en brouillon peut être validée.")
        self.status = VenteStatus.VALIDATED
        self.save(update_fields=['status', 'updated_at'])
