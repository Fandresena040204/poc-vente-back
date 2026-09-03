from rest_framework import serializers

from apps.ventes.models import VenteLigne


class VenteLigneSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)

    class Meta:
        model = VenteLigne
        fields = ['id', 'product', 'quantity', 'unit_price']
