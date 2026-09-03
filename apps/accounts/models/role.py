from django.db import models

from apps.core.utils import generate_reference


class Role(models.Model):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('role_id_seq', 'ROL')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
