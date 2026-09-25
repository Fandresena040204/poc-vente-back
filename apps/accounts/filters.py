from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from apps.accounts.models import Customer
from apps.core.filters import CharInFilter

User = get_user_model()


class UserFilterSet(filters.FilterSet):
    roles = CharInFilter(field_name='roles__name')

    class Meta:
        model = User
        fields = ['roles']


class CustomerFilterSet(filters.FilterSet):
    is_active = filters.BooleanFilter(field_name='is_active')
    city = CharInFilter(field_name='city')

    class Meta:
        model = Customer
        fields = ['is_active', 'city']
