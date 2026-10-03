from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)
    permissions = serializers.SerializerMethodField()
    permission_overrides = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'roles', 'permissions', 'permission_overrides',
        ]
        read_only_fields = ['id', 'username', 'roles', 'permissions', 'permission_overrides']

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_permissions(self, obj):
        codenames = {c for c in obj.roles.values_list('permissions__codename', flat=True) if c}
        for override in obj.permission_overrides.select_related('permission'):
            if override.is_allowed:
                codenames.add(override.permission.codename)
            else:
                codenames.discard(override.permission.codename)
        return sorted(codenames)

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_permission_overrides(self, obj):
        return [
            {'permission': o.permission.codename, 'is_allowed': o.is_allowed}
            for o in obj.permission_overrides.select_related('permission')
        ]
