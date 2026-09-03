from django.db import models

from apps.core.models import TimestampedModel


class Customer(TimestampedModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
