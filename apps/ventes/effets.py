"""Effets de bord des étapes de `VENTE_WORKFLOW` (voir apps/ventes/workflow.py).

Chaque fonction a la signature `(vente, user) -> None` et s'exécute dans la
même transaction que le changement de statut (`WorkflowMixin.transition`,
apps/accounts/workflow.py) : si elle lève une exception, le statut est
annulé avec le reste de la transaction. Une fonction ne décide jamais du
statut : elle fait seulement le travail métier.
"""

from apps.ventes.models import Livraison


def apres_validation_dg(vente, user):
    """La validation finale (DG) déclenche la préparation de la livraison."""
    Livraison.objects.create(vente=vente, address=vente.customer.address)
