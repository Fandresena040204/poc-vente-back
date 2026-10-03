from rest_framework import serializers

from apps.ventes.models import VenteLigneListView


class VenteLigneReadSerializer(serializers.ModelSerializer):
    """Backed by `VenteLigneListView` (DB view) — `product_name`/`product_sku`
    come from the view's join, not a per-request lookup or a client-side
    fetch-everything-and-resolve."""

    class Meta:
        model = VenteLigneListView
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity', 'unit_price',
            'discount_percent', 'tva_rate',
        ]
