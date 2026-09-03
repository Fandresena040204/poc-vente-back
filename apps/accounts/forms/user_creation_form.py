from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm

from apps.accounts.models import User


class UserCreationForm(DjangoUserCreationForm):
    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = ('username',)
