from rest_framework import viewsets

from apps.accounts.permissions import HasRolePermission
from apps.ventes.filters import LivraisonFilterSet
from apps.ventes.models import Livraison
from apps.ventes.serializers import LivraisonSerializer


class LivraisonViewSet(viewsets.ModelViewSet):
    serializer_class = LivraisonSerializer
    permission_classes = [HasRolePermission]
    filterset_class = LivraisonFilterSet
    ordering_fields = ['delivery_date', 'created_at']

    def get_queryset(self):
        return Livraison.objects.select_related('vente')
