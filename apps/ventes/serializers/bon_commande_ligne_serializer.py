from rest_framework import serializers

from apps.ventes.models import BonCommandeLigne


class BonCommandeLigneSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)

    class Meta:
        model = BonCommandeLigne
        fields = ['id', 'product', 'quantity', 'unit_price', 'discount_percent', 'tva_rate']
