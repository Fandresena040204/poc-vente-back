from django.contrib import admin

from apps.ventes.models import VenteLigne


class VenteLigneInline(admin.TabularInline):
    model = VenteLigne
    extra = 0
