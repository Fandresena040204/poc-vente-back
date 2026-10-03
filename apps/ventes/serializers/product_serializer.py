from rest_framework import serializers

from apps.ventes.models import Product


class ProductSerializer(serializers.ModelSerializer):
    """Write-only path (`create`/`update`) — `ProductViewSet.list`/`retrieve`
    use `ProductReadSerializer` (backed by the `ProductListView` DB view)
    instead, so this doesn't need a `category_name` resolved field."""

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'default_price', 'category', 'description',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
