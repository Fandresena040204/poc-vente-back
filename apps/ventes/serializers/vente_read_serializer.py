from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.permissions.has_role_permission import HasRolePermission
from apps.accounts.workflow import allowed_steps_from_codenames
from apps.ventes.models import Vente, VenteListView
from apps.ventes.serializers.vente_ligne_read_serializer import VenteLigneReadSerializer
from apps.ventes.workflow import VENTE_WORKFLOW


class VenteReadSerializer(serializers.ModelSerializer):
    """Backed by `VenteListView` (DB view) — used for `list`/`retrieve` only
    (`VenteViewSet.get_serializer_class`). `customer_name` comes from the
    view's join; `create`/`update`/workflow transitions go through the
    writable `Vente` model instead."""

    lines = VenteLigneReadSerializer(many=True, read_only=True)
    # Étapes de VENTE_WORKFLOW jouables par l'utilisateur courant depuis ce
    # statut — le front n'affiche que ces boutons (voir
    # apps/accounts/workflow.py:allowed_steps_from_codenames).
    allowed_steps = serializers.SerializerMethodField()

    class Meta:
        model = VenteListView
        fields = [
            'id', 'customer', 'customer_name', 'status', 'priority', 'currency', 'discount_percent',
            'subtotal_ht', 'discount_amount', 'tva_amount', 'total',
            'expected_delivery_date', 'notes', 'lines',
            'achat_par', 'achat_le', 'caisse_par', 'caisse_le', 'dg_par', 'dg_le',
            'allowed_steps', 'created_at', 'updated_at',
        ]

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_allowed_steps(self, obj):
        request = self.context.get('request')
        if request is None:
            return []
        # Calculé une seule fois par requête (deux requêtes SQL), pas une
        # fois par règle et par ligne (N+1) — un même `VenteReadSerializer`
        # (même `self`) traite toutes les lignes d'une page.
        if not hasattr(self, '_vente_codenames'):
            # `effective_codenames` checks permissions against the real
            # `Vente` model (`view_vente`-style codenames), not
            # `VenteListView` — `obj` here is only read from the DB view.
            self._vente_codenames = HasRolePermission.effective_codenames(request.user, Vente)
        return allowed_steps_from_codenames(obj.status, VENTE_WORKFLOW, self._vente_codenames)
