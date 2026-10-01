from django.db import transaction
from rest_framework import serializers

from apps.ventes.models import BonCommande, BonCommandeLigne
from apps.ventes.serializers.bon_commande_ligne_serializer import BonCommandeLigneSerializer


class BonCommandeSerializer(serializers.ModelSerializer):
    lines = BonCommandeLigneSerializer(many=True)

    class Meta:
        model = BonCommande
        fields = [
            'id', 'customer', 'currency', 'discount_percent',
            'expected_delivery_date', 'lines', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError(
                "Un bon de commande doit contenir au moins une ligne."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        bon_commande = BonCommande.objects.create(
            created_by=self.context['request'].user,
            **validated_data,
        )
        for line_data in lines_data:
            line_data.pop('id', None)
            BonCommandeLigne.objects.create(bon_commande=bon_commande, **line_data)
        return bon_commande

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
                    BonCommandeLigne.objects.filter(
                        id=line_id, bon_commande=instance
                    ).update(**line_data)
                else:
                    BonCommandeLigne.objects.create(bon_commande=instance, **line_data)

        return instance
