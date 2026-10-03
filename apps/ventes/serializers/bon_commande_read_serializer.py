from rest_framework import serializers

from apps.ventes.models import BonCommandeLigneListView, BonCommandeListView


class BonCommandeLigneReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BonCommandeLigneListView
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'discount_percent', 'tva_rate',
        ]


class BonCommandeReadSerializer(serializers.ModelSerializer):
    lines = BonCommandeLigneReadSerializer(many=True, read_only=True)

    class Meta:
        model = BonCommandeListView
        fields = [
            'id', 'customer', 'customer_name', 'currency', 'discount_percent',
            'expected_delivery_date', 'lines', 'created_at', 'updated_at',
        ]
