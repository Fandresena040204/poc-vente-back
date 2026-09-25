from django.db import models

from apps.core.models import TimestampedModel
from apps.core.utils import generate_reference


class ProductCategory(TimestampedModel):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'product categories'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('product_category_id_seq', 'CAT')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
