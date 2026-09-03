from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import CustomerViewSet, MeView, RegisterView, RoleViewSet, UserViewSet

router = DefaultRouter()
router.register('customers', CustomerViewSet, basename='customer')
router.register('roles', RoleViewSet, basename='role')
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', MeView.as_view(), name='me'),
] + router.urls
