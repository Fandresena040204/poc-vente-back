from django.contrib import admin

from apps.ventes.models import Paiement


class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 0
