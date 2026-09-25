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


class VenteCurrency(models.TextChoices):
    MGA = 'MGA', 'Ariary malgache'
    EUR = 'EUR', 'Euro'
    USD = 'USD', 'Dollar américain'


class Vente(AuditedModel):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='ventes')
    status = FSMField(default=VenteStatus.DRAFT, choices=VenteStatus.choices)
    priority = models.CharField(
        max_length=10, choices=VentePriority.choices, default=VentePriority.NORMAL
    )
    currency = models.CharField(
        max_length=3, choices=VenteCurrency.choices, default=VenteCurrency.MGA
    )
    # HT = hors taxe (before VAT); TTC = toutes taxes comprises (after VAT).
    # `total` is the grand total (TTC): subtotal_ht (sum of lines, each net
    # of its own discount_percent) minus the global discount, plus VAT.
    subtotal_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tva_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
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
        lines = list(self.lines.all())

        def line_ht(line):
            return line.quantity * line.unit_price * (hundred - line.discount_percent) / hundred

        subtotal_ht = sum((line_ht(line) for line in lines), start=Decimal('0'))
        discount_amount = subtotal_ht * self.discount_percent / hundred
        global_discount_ratio = (hundred - self.discount_percent) / hundred
        tva_amount = sum(
            (line_ht(line) * global_discount_ratio * line.tva_rate / hundred for line in lines),
            start=Decimal('0'),
        )
        net_ht = subtotal_ht - discount_amount
        total = net_ht + tva_amount

        self.subtotal_ht = subtotal_ht.quantize(Decimal('0.01'))
        self.discount_amount = discount_amount.quantize(Decimal('0.01'))
        self.tva_amount = tva_amount.quantize(Decimal('0.01'))
        self.total = total.quantize(Decimal('0.01'))
        self.save(
            update_fields=['subtotal_ht', 'discount_amount', 'tva_amount', 'total', 'updated_at']
        )

    @transition(field=status, source=VenteStatus.DRAFT, target=VenteStatus.VALIDATED)
    def validate_vente(self):
        pass

    @transition(field=status, source=VenteStatus.VALIDATED, target=VenteStatus.CANCELLED)
    def cancel_vente(self):
        pass
