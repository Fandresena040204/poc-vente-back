from rest_framework import serializers

from apps.ventes.models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'default_price']
