from django.contrib.auth.models import Permission
from rest_framework import serializers

from apps.accounts.models import Role


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        slug_field='codename', many=True, queryset=Permission.objects.all(), required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions']
