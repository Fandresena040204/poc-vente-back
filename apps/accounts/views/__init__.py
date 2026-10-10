from apps.accounts.views.customer_viewset import CustomerViewSet
from apps.accounts.views.me_view import MeView
from apps.accounts.views.register_view import RegisterView
from apps.accounts.views.role_viewset import RoleViewSet
from apps.accounts.views.token_view import LoggingTokenObtainPairView
from apps.accounts.views.user_viewset import UserViewSet

__all__ = [
    'CustomerViewSet', 'LoggingTokenObtainPairView', 'MeView', 'RegisterView', 'RoleViewSet',
    'UserViewSet',
]
