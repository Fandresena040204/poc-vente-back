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


class VentePriority(models.TextChoices):
    LOW = 'low', 'Basse'
    NORMAL = 'normal', 'Normale'
    HIGH = 'high', 'Haute'


class Vente(AuditedModel):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='ventes')
    status = FSMField(default=VenteStatus.DRAFT, choices=VenteStatus.choices)
    priority = models.CharField(
        max_length=10, choices=VentePriority.choices, default=VentePriority.NORMAL
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    expected_delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('vente_id_seq', 'VNT')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Vente #{self.pk} - {self.customer}'

    def recalculate_total(self):
        hundred = Decimal('100')
        subtotal = sum(
            (
                line.quantity
                * line.unit_price
                * (hundred - line.discount_percent)
                / hundred
                for line in self.lines.all()
            ),
            start=Decimal('0'),
        )
        total = subtotal * (hundred - self.discount_percent) / hundred
        self.total = total.quantize(Decimal('0.01'))
        self.save(update_fields=['total', 'updated_at'])

    @transition(field=status, source=VenteStatus.DRAFT, target=VenteStatus.VALIDATED)
    def validate_vente(self):
        pass

    @transition(field=status, source=VenteStatus.VALIDATED, target=VenteStatus.CANCELLED)
    def cancel_vente(self):
        pass
