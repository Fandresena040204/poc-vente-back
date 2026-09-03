from django.contrib import admin

from apps.ventes.models import Product, Vente, VenteLigne


class VenteLigneInline(admin.TabularInline):
    model = VenteLigne
    extra = 0


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'total', 'created_at']
    list_filter = ['status']
    inlines = [VenteLigneInline]


admin.site.register(Product)
