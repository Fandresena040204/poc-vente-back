from django.contrib import admin

from apps.ventes.models import Livraison


class LivraisonInline(admin.TabularInline):
    model = Livraison
    extra = 0
