from django.db import models

from apps.core.models import TimestampedModel


class Product(TimestampedModel):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
    default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
