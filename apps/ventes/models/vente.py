from decimal import Decimal

from django.db import models
from django_fsm import FSMField, transition

from apps.accounts.models import Customer
from apps.core.models import AuditedModel
from apps.core.utils import generate_reference


class VenteStatus(models.TextChoices):
    DRAFT = 'draft', 'Brouillon'
    VALIDATED = 'validated', 'Validée'
    CANCELLED = 'cancelled', 'Annulée'


class Vente(AuditedModel):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='ventes')
    status = FSMField(default=VenteStatus.DRAFT, choices=VenteStatus.choices)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('vente_id_seq', 'VNT')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Vente #{self.pk} - {self.customer}'

    def recalculate_total(self):
        total = self.lines.aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_price'))
        )['total'] or Decimal('0')
        self.total = total
        self.save(update_fields=['total', 'updated_at'])

    @transition(field=status, source=VenteStatus.DRAFT, target=VenteStatus.VALIDATED)
    def validate_vente(self):
        pass

    @transition(field=status, source=VenteStatus.VALIDATED, target=VenteStatus.CANCELLED)
    def cancel_vente(self):
        pass
