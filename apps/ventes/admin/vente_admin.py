from django.contrib import admin

from apps.ventes.admin.vente_ligne_inline import VenteLigneInline
from apps.ventes.models import Vente


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'total', 'created_at']
    list_filter = ['status']
    inlines = [VenteLigneInline]
