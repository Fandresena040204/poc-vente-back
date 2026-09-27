from rest_framework import serializers

from apps.ventes.models import ProductListView


class ProductReadSerializer(serializers.ModelSerializer):
    """Backed by `ProductListView` (DB view) — used for `list`/`retrieve`
    only (`ProductViewSet.get_serializer_class`). `category_name` comes
    from the view's join; `create`/`update`/`destroy` go through the
    writable `Product` model + `ProductSerializer` instead."""

    class Meta:
        model = ProductListView
        fields = [
            'id', 'name', 'sku', 'default_price', 'category', 'category_name', 'description',
            'is_active', 'created_at', 'updated_at',
        ]
