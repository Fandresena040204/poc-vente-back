from rest_framework import serializers

from apps.ventes.models import VenteLigne


class VenteLigneSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    # Same reasoning as Vente.customer_name: avoids the frontend fetching
    # every Product just to resolve a line's `product` id to a label.
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = VenteLigne
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity', 'unit_price',
            'discount_percent', 'tva_rate',
        ]
