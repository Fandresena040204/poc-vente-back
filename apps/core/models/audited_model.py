from django.conf import settings
from django.db import models

from apps.core.models.timestamped_model import TimestampedModel


class AuditedModel(TimestampedModel):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    class Meta:
        abstract = True
