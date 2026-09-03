from django.db import transaction
from rest_framework import serializers

from apps.ventes.models import Product, Vente, VenteLigne


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'default_price']


class VenteLigneSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = VenteLigne
        fields = ['id', 'product', 'quantity', 'unit_price']


class VenteSerializer(serializers.ModelSerializer):
    lines = VenteLigneSerializer(many=True)

    class Meta:
        model = Vente
        fields = ['id', 'customer', 'status', 'total', 'lines', 'created_at', 'updated_at']
        read_only_fields = ['status', 'total', 'created_at', 'updated_at']

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError("Une vente doit contenir au moins une ligne.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        vente = Vente.objects.create(
            created_by=self.context['request'].user,
            **validated_data,
        )
        for line_data in lines_data:
            line_data.pop('id', None)
            VenteLigne.objects.create(vente=vente, **line_data)
        return vente

    @transaction.atomic
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lines_data is not None:
            existing_ids = {line.id for line in instance.lines.all()}
            sent_ids = {line_data['id'] for line_data in lines_data if 'id' in line_data}

            instance.lines.filter(id__in=existing_ids - sent_ids).delete()

            for line_data in lines_data:
                line_id = line_data.pop('id', None)
                if line_id and line_id in existing_ids:
                    VenteLigne.objects.filter(id=line_id, vente=instance).update(**line_data)
                else:
                    VenteLigne.objects.create(vente=instance, **line_data)

        instance.refresh_from_db()
        return instance
