from django.db import models


class VenteStatus(models.IntegerChoices):
    """Le statut porte l'ordre du workflow : un niveau supérieur rend les
    niveaux inférieurs non joués "sautés" (ex. VALIDE_CAISSE depuis CREE
    saute l'achat), et un rejet (négatif) est terminal. Les écarts entre
    valeurs (1, 3, 6, 9) laissent de la place pour une étape future sans
    renuméroter. Séparé de `apps.ventes.models.vente` pour que ce fichier
    et `VENTE_WORKFLOW` ci-dessous n'importent jamais le modèle (évite un
    import circulaire : `Vente.Meta.permissions` se construit à partir de
    `VENTE_WORKFLOW`)."""

    CREE = 1, 'Brouillon'
    VALIDE_ACHAT = 3, 'Validée (achat)'
    VALIDE_CAISSE = 6, 'Validée (caisse)'
    VALIDE_DG = 9, 'Validée (DG)'
    ANNULEE = -1, 'Annulée'
    REJETEE_ACHAT = -3, 'Rejetée (achat)'
    REJETEE_CAISSE = -6, 'Rejetée (caisse)'
    REJETEE_DG = -9, 'Rejetée (DG)'


# Déclaration du workflow de la vente, lue par `apps.accounts.workflow.
# WorkflowMixin` (générique, ne connaît rien de la vente). Chaque règle :
# - 'step' : le nom utilisé dans l'URL `transition/{step}/`.
# - 'permission' : le codename requis (voir `Vente.Meta.permissions`, qui
#   se construit à partir de cette liste — une seule source de vérité).
# - 'from' : les statuts depuis lesquels la transition est acceptée.
# - 'to' : le statut cible.
# - 'effet' (optionnel) : chemin(s) de fonction(s) `(vente, user) -> None`
#   exécutée(s) après le changement de statut, dans la même transaction
#   (voir apps/ventes/effets.py).
VENTE_WORKFLOW = [
    {
        'step': 'valider_achat',
        'permission': 'validate_achat_vente',
        'from': [VenteStatus.CREE],
        'to': VenteStatus.VALIDE_ACHAT,
        'effet': 'apps.ventes.effets.enregistrer_achat',
    },
    {
        'step': 'rejeter_achat',
        'permission': 'reject_achat_vente',
        'from': [VenteStatus.CREE],
        'to': VenteStatus.REJETEE_ACHAT,
        'effet': 'apps.ventes.effets.enregistrer_achat',
    },
    {
        'step': 'valider_caisse',
        'permission': 'validate_caisse_vente',
        'from': [VenteStatus.CREE, VenteStatus.VALIDE_ACHAT],
        'to': VenteStatus.VALIDE_CAISSE,
        'effet': 'apps.ventes.effets.enregistrer_caisse',
    },
    {
        'step': 'rejeter_caisse',
        'permission': 'reject_caisse_vente',
        'from': [VenteStatus.CREE, VenteStatus.VALIDE_ACHAT],
        'to': VenteStatus.REJETEE_CAISSE,
        'effet': 'apps.ventes.effets.enregistrer_caisse',
    },
    {
        'step': 'valider_dg',
        'permission': 'validate_dg_vente',
        'from': [VenteStatus.CREE, VenteStatus.VALIDE_ACHAT, VenteStatus.VALIDE_CAISSE],
        'to': VenteStatus.VALIDE_DG,
        'effet': [
            'apps.ventes.effets.enregistrer_dg',
            'apps.ventes.effets.apres_validation_dg',
        ],
    },
    {
        'step': 'rejeter_dg',
        'permission': 'reject_dg_vente',
        'from': [VenteStatus.CREE, VenteStatus.VALIDE_ACHAT, VenteStatus.VALIDE_CAISSE],
        'to': VenteStatus.REJETEE_DG,
        'effet': 'apps.ventes.effets.enregistrer_dg',
    },
    {
        'step': 'annuler',
        'permission': 'cancel_vente',
        'from': [VenteStatus.CREE],
        'to': VenteStatus.ANNULEE,
    },
]
