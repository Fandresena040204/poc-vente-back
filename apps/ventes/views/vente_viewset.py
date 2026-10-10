from rest_framework import viewsets

from apps.accounts.permissions import HasRolePermission
from apps.accounts.workflow import WorkflowMixin
from apps.ventes.filters import VenteFilterSet
from apps.ventes.models import Vente, VenteListView
from apps.ventes.serializers import VenteReadSerializer, VenteSerializer
from apps.ventes.workflow import VENTE_WORKFLOW


class VenteViewSet(WorkflowMixin, viewsets.ModelViewSet):
    # Stays `VenteSerializer` (not overridden per-action) so
    # `HasRolePermission` — which reads `view.serializer_class.Meta.model`,
    # not `get_serializer_class()` — keeps deriving `{action}_vente`
    # codenames against the real `Vente` model, not the read-only view.
    serializer_class = VenteSerializer
    permission_classes = [HasRolePermission]
    # No `search_fields`: `id` is its own filter (VenteFilterSet) rather
    # than the global `search=`.
    ordering_fields = ['created_at', 'total', 'priority', 'expected_delivery_date']

    # WorkflowMixin (apps/accounts/workflow.py) : `transition`/`allowed-steps`
    # check permissions against the real `Vente`, not `VenteListView`, so
    # `workflow_model` is set explicitly — `get_queryset().model` would be
    # wrong for `list`/`retrieve`.
    workflow = VENTE_WORKFLOW
    workflow_model = Vente

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
        # `list`/`retrieve` read from the `vente_list_view` DB view
        # (customer_name/product_name/product_sku already resolved in SQL —
        # see VenteListView/VenteLigneListView and migration 0008) instead
        # of the writable model + `select_related`/`prefetch_related`.
        # `create`/`update`/workflow transitions still need the real,
        # writable `Vente`.
        if self.action in ('list', 'retrieve'):
            return VenteListView.objects.prefetch_related('lines')
        return (
            Vente.objects.select_related('customer', 'created_by')
            .prefetch_related('lines__product')
        )
