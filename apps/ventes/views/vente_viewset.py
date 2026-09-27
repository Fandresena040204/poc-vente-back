from django_fsm import TransitionNotAllowed
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import HasRolePermission
from apps.ventes.filters import VenteFilterSet
from apps.ventes.models import Vente, VenteListView
from apps.ventes.serializers import VenteReadSerializer, VenteSerializer


class VenteViewSet(viewsets.ModelViewSet):
    # Stays `VenteSerializer` (not overridden per-action) so
    # `HasRolePermission` — which reads `view.serializer_class.Meta.model`,
    # not `get_serializer_class()` — keeps deriving `{action}_vente`
    # codenames against the real `Vente` model, not the read-only view.
    serializer_class = VenteSerializer
    permission_classes = [HasRolePermission]
    # No `search_fields`: `id` is its own filter (VenteFilterSet) rather
    # than the global `search=`.
    ordering_fields = ['created_at', 'total', 'priority', 'expected_delivery_date']

    @property
    def filterset_class(self):
        # django-filter asserts `filterset.Meta.model` matches
        # `queryset.model` exactly — since `get_queryset()` below returns a
        # different model for 'list' (VenteListView) than for every other
        # action (Vente), filtering only makes sense for 'list' anyway
        # (nobody filters a single detail-by-pk fetch).
        return VenteFilterSet if self.action == 'list' else None

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return VenteReadSerializer
        return VenteSerializer

    def get_queryset(self):
        # `list`/`retrieve` read from the `ventes_vente_list_view` DB view
        # (customer_name/product_name/product_sku already resolved in SQL —
        # see VenteListView/VenteLigneListView and migration 0007) instead
        # of the writable model + `select_related`/`prefetch_related`.
        # `create`/`update`/`valider`/`annuler` still need the real,
        # writable `Vente` (FSM transitions, `recalculate_total`, ...).
        if self.action in ('list', 'retrieve'):
            return VenteListView.objects.prefetch_related('lines')
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
