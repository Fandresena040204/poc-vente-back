from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_superuser', 'roles']
        read_only_fields = ['id', 'username', 'is_superuser', 'roles']
