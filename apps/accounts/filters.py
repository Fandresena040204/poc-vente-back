from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from apps.core.filters import CharInFilter

User = get_user_model()


class UserFilterSet(filters.FilterSet):
    roles = CharInFilter(field_name='roles__name')

    class Meta:
        model = User
        fields = ['roles']
