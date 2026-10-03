from rest_framework import serializers

from apps.ventes.models import Livraison


class LivraisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Livraison
        fields = [
            'id', 'vente', 'status', 'delivery_date', 'address',
            'tracking_number', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
