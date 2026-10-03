from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.ventes.models import VenteLigne


@receiver(post_save, sender=VenteLigne)
def recalculate_total_on_save(sender, instance, **kwargs):
    instance.vente.recalculate_total()


@receiver(post_delete, sender=VenteLigne)
def recalculate_total_on_delete(sender, instance, **kwargs):
    instance.vente.recalculate_total()
