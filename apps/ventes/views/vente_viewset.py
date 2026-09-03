from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import HasRolePermission
from apps.ventes.models import Vente
from apps.ventes.serializers import VenteSerializer


class VenteViewSet(viewsets.ModelViewSet):
    serializer_class = VenteSerializer
    permission_classes = [HasRolePermission]
    filterset_fields = ['status', 'customer']
    search_fields = ['customer__name']
    ordering_fields = ['created_at', 'total']

    def get_queryset(self):
        return (
            Vente.objects.select_related('customer', 'created_by')
            .prefetch_related('lines__product')
        )

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        vente = self.get_object()
        try:
            vente.validate_vente()
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)
        return Response(VenteSerializer(vente, context={'request': request}).data)
