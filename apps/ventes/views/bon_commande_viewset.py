from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import HasRolePermission
from apps.ventes.models import BonCommande
from apps.ventes.serializers import BonCommandeSerializer


class BonCommandeViewSet(viewsets.ModelViewSet):
    serializer_class = BonCommandeSerializer
    permission_classes = [HasRolePermission]
    ordering_fields = ['created_at']

    def get_queryset(self):
        return BonCommande.objects.select_related('customer').prefetch_related('lines__product')

    @action(detail=True, methods=['get'])
    def to_vente_defaults(self, request, pk=None):
        bon = self.get_object()
        return Response({
            'customer': bon.customer_id,
            'currency': bon.currency,
            'discount_percent': bon.discount_percent,
            'expected_delivery_date': bon.expected_delivery_date,
            'lines': [
                {
                    'product': line.product_id,
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                    'discount_percent': line.discount_percent,
                    'tva_rate': line.tva_rate,
                }
                for line in bon.lines.all()
            ],
        })
