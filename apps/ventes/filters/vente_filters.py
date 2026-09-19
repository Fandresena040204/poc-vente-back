from django_filters import rest_framework as filters

from apps.core.filters import CharInFilter
from apps.ventes.models import Vente


class VenteFilterSet(filters.FilterSet):
    status = CharInFilter(field_name='status')

    class Meta:
        model = Vente
        fields = ['status', 'customer']
