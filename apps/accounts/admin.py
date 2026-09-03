from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.forms import UserChangeForm, UserCreationForm
from apps.accounts.models import Customer, Role, User


class UserAdmin(DjangoUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'roles')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'email', 'password1', 'password2', 'is_staff'),
            },
        ),
    )
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    list_filter = ['is_staff', 'is_active']
    filter_horizontal = ('roles',)
    ordering = ['username']


class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    filter_horizontal = ('permissions',)


admin.site.register(Customer)
admin.site.register(Role, RoleAdmin)
admin.site.register(User, UserAdmin)
