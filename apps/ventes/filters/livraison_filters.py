from django_filters import rest_framework as filters

from apps.core.filters import CharInFilter
from apps.ventes.models import Livraison


class LivraisonFilterSet(filters.FilterSet):
    status = CharInFilter(field_name='status')

    class Meta:
        model = Livraison
        fields = ['status', 'vente']
