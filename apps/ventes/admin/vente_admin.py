from django.contrib import admin

from apps.ventes.admin.livraison_inline import LivraisonInline
from apps.ventes.admin.paiement_inline import PaiementInline
from apps.ventes.admin.vente_ligne_inline import VenteLigneInline
from apps.ventes.models import Vente


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'priority', 'total', 'created_at']
    list_filter = ['status', 'priority']
    inlines = [VenteLigneInline, LivraisonInline, PaiementInline]
