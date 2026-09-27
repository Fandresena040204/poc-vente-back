from rest_framework import serializers

from apps.ventes.models import VenteLigne


class VenteLigneSerializer(serializers.ModelSerializer):
    """Write-only path, nested in `VenteSerializer` — `product_name`/
    `product_sku` aren't needed here, `VenteLigneReadSerializer` (backed by
    the `VenteLigneListView` DB view) carries those for `list`/`retrieve`."""

    id = serializers.CharField(required=False)

    class Meta:
        model = VenteLigne
        fields = ['id', 'product', 'quantity', 'unit_price', 'discount_percent', 'tva_rate']
