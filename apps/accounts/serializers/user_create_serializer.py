from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import Role

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """`UserViewSet.create` only — distinct from `RegisterSerializer`
    (public self sign-up, apps/accounts/views/register_view.py) in that it
    lets the creator assign roles right away, and is reached through
    `HasRolePermission` (`add_user` + `view_user`), not `AllowAny`."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    roles = serializers.SlugRelatedField(
        slug_field='name', many=True, queryset=Role.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'roles', 'is_active']
        read_only_fields = ['id']

    def create(self, validated_data):
        roles = validated_data.pop('roles', [])
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        if roles:
            user.roles.set(roles)
        return user
