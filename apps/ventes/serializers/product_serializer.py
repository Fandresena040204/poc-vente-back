from rest_framework import serializers

from apps.ventes.models import Product


class ProductSerializer(serializers.ModelSerializer):
    # `category` is nullable, so a plain `source='category.name'` CharField
    # would blow up on products without one — SerializerMethodField instead.
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'default_price', 'category', 'category_name', 'description',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
