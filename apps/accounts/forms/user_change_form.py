from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm

from apps.accounts.models import User


class UserChangeForm(DjangoUserChangeForm):
    class Meta(DjangoUserChangeForm.Meta):
        model = User
        fields = '__all__'
