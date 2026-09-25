from rest_framework import viewsets

from apps.accounts.permissions import HasRolePermission
from apps.ventes.filters import PaiementFilterSet
from apps.ventes.models import Paiement
from apps.ventes.serializers import PaiementSerializer


class PaiementViewSet(viewsets.ModelViewSet):
    serializer_class = PaiementSerializer
    permission_classes = [HasRolePermission]
    filterset_class = PaiementFilterSet
    ordering_fields = ['paid_at', 'amount', 'created_at']

    def get_queryset(self):
        return Paiement.objects.select_related('vente')
