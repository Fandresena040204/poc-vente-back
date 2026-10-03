from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group

from apps.accounts.forms import UserChangeForm, UserCreationForm
from apps.accounts.models import Customer, Role, User

# Django's auth app registers Group in the admin as a side effect of
# importing django.contrib.auth.admin (above) — unregister it since the
# underlying auth_group table is dropped (migration 0010): Role replaces
# Group here, and leaving this registered would 500 on /admin/auth/group/.
admin.site.unregister(Group)


class UserAdmin(DjangoUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'roles')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'email', 'password1', 'password2'),
            },
        ),
    )
    list_display = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['is_active']
    filter_horizontal = ('roles',)
    ordering = ['username']


class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    filter_horizontal = ('permissions',)


admin.site.register(Customer)
admin.site.register(Role, RoleAdmin)
admin.site.register(User, UserAdmin)
