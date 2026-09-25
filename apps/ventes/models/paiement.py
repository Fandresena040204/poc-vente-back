from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel
from apps.core.utils import generate_reference
from apps.ventes.models.vente import Vente


class PaiementMethod(models.TextChoices):
    CASH = 'cash', 'Espèces'
    CARD = 'card', 'Carte'
    TRANSFER = 'transfer', 'Virement'


class Paiement(TimestampedModel):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='paiements')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(
        max_length=20, choices=PaiementMethod.choices, default=PaiementMethod.CASH
    )
    paid_at = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-paid_at']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('paiement_id_seq', 'PAY')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Paiement {self.id} - {self.vente_id}'
