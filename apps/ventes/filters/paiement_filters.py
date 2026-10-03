from django_filters import rest_framework as filters

from apps.core.filters import CharInFilter
from apps.ventes.models import Paiement


class PaiementFilterSet(filters.FilterSet):
    method = CharInFilter(field_name='method')

    class Meta:
        model = Paiement
        fields = ['method', 'vente']
