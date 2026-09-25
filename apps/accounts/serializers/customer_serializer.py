from rest_framework import serializers

from apps.accounts.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'email', 'phone', 'address', 'city', 'birth_date',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
