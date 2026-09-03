from django.db import models

from apps.core.models import TimestampedModel
from apps.core.utils import generate_reference


class Customer(TimestampedModel):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('customer_id_seq', 'CUS')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
