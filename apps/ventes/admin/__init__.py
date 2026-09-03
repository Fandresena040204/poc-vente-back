from apps.ventes.admin.product_admin import *  # noqa: F401,F403
from apps.ventes.admin.vente_admin import VenteAdmin
from apps.ventes.admin.vente_ligne_inline import VenteLigneInline

__all__ = ['VenteAdmin', 'VenteLigneInline']
