from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(
        source='groups', slug_field='name', many=True, read_only=True
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'is_staff', 'roles']
        read_only_fields = fields
