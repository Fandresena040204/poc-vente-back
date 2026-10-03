from rest_framework import serializers

from apps.ventes.models import VenteListView
from apps.ventes.serializers.vente_ligne_read_serializer import VenteLigneReadSerializer


class VenteReadSerializer(serializers.ModelSerializer):
    """Backed by `VenteListView` (DB view) — used for `list`/`retrieve` only
    (`VenteViewSet.get_serializer_class`). `customer_name` comes from the
    view's join; `create`/`update`/`valider`/`annuler` go through the
    writable `Vente` model + `VenteSerializer` instead."""

    lines = VenteLigneReadSerializer(many=True, read_only=True)

    class Meta:
        model = VenteListView
        fields = [
            'id', 'customer', 'customer_name', 'status', 'priority', 'currency', 'discount_percent',
            'subtotal_ht', 'discount_amount', 'tva_amount', 'total',
            'expected_delivery_date', 'notes', 'lines', 'created_at', 'updated_at',
        ]
