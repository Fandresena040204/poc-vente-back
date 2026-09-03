from django.db import models

from apps.core.models import TimestampedModel
from apps.core.utils import generate_reference


class Product(TimestampedModel):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
    default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('product_id_seq', 'PRD')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
