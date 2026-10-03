from rest_framework import serializers

from apps.ventes.models import Paiement


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = [
            'id', 'vente', 'amount', 'method', 'paid_at', 'reference', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
