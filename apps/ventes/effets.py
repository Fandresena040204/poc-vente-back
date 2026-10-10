"""Effets de bord des étapes de `VENTE_WORKFLOW` (voir apps/ventes/workflow.py).

Chaque fonction a la signature `(vente, user) -> None` et s'exécute dans la
même transaction que le changement de statut (`WorkflowMixin.transition`,
apps/accounts/workflow.py) : si elle lève une exception, le statut est
annulé avec le reste de la transaction. Une fonction ne décide jamais du
statut : elle fait seulement le travail métier.
"""

from django.utils import timezone

from apps.ventes.models import Livraison


def enregistrer_achat(vente, user):
    vente.achat_par = user
    vente.achat_le = timezone.now()
    vente.save(update_fields=['achat_par', 'achat_le'])


def enregistrer_caisse(vente, user):
    vente.caisse_par = user
    vente.caisse_le = timezone.now()
    vente.save(update_fields=['caisse_par', 'caisse_le'])


def enregistrer_dg(vente, user):
    vente.dg_par = user
    vente.dg_le = timezone.now()
    vente.save(update_fields=['dg_par', 'dg_le'])


def apres_validation_dg(vente, user):
    """La validation finale (DG) déclenche la préparation de la livraison."""
    Livraison.objects.create(vente=vente, address=vente.customer.address)
