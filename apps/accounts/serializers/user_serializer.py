from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'roles', 'permissions']
        read_only_fields = ['id', 'username', 'roles', 'permissions']

    def get_permissions(self, obj):
        codenames = obj.roles.values_list('permissions__codename', flat=True)
        return sorted({codename for codename in codenames if codename})
