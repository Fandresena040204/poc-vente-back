from django.db import models

from apps.core.utils import generate_reference


class Permission(models.Model):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    codename = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'permission'
        constraints = [
            models.UniqueConstraint(
                fields=['app_label', 'model', 'codename'], name='permission_unique_codename'
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_reference('permission_id_seq', 'PRM')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.codename
