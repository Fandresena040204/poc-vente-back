from django_fsm import TransitionNotAllowed
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
        except TransitionNotAllowed:
            return Response(
                {'detail': "Seule une vente en brouillon peut être validée."}, status=400
            )
        vente.save(update_fields=['status', 'updated_at'])
        return Response(VenteSerializer(vente, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        vente = self.get_object()
        try:
            vente.cancel_vente()
        except TransitionNotAllowed:
            return Response(
                {'detail': "Seule une vente validée peut être annulée."}, status=400
            )
        vente.save(update_fields=['status', 'updated_at'])
        return Response(VenteSerializer(vente, context={'request': request}).data)
