from django.db import models

from apps.core.models import TimestampedModel
from apps.core.utils import generate_reference
from apps.ventes.models.vente import Vente


class LivraisonStatus(models.TextChoices):
    PENDING = 'pending', 'En attente'
    SHIPPED = 'shipped', 'Expédiée'
    DELIVERED = 'delivered', 'Livrée'


class Livraison(TimestampedModel):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='livraisons')
    status = models.CharField(
        max_length=20, choices=LivraisonStatus.choices, default=LivraisonStatus.PENDING
    )
    delivery_date = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    tracking_number = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('livraison_id_seq', 'LIV')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Livraison {self.id} - {self.vente_id}'
