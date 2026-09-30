from rest_framework import serializers

from apps.ventes.models import Fournisseur


class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ['id', 'name', 'email', 'is_active']
