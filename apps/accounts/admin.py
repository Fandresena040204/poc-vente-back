from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import Customer, Role, User

admin.site.register(Customer)
admin.site.register(Role)
admin.site.register(User, DjangoUserAdmin)
