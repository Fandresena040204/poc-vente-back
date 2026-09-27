from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from apps.accounts.models import Customer, Role
from apps.core.filters import CharInFilter

User = get_user_model()


class UserFilterSet(filters.FilterSet):
    username = filters.CharFilter(field_name='username', lookup_expr='icontains')
    roles = CharInFilter(field_name='roles__name')

    class Meta:
        model = User
        fields = ['username', 'roles']


class CustomerFilterSet(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    email = filters.CharFilter(field_name='email', lookup_expr='icontains')
    is_active = filters.BooleanFilter(field_name='is_active')
    city = CharInFilter(field_name='city')

    class Meta:
        model = Customer
        fields = ['name', 'email', 'is_active', 'city']


class RoleFilterSet(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Role
        fields = ['name']
