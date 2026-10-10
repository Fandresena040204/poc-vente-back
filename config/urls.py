from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoggingTokenObtainPairView
from apps.core.views import AuditLogViewSet, MetaView, PermissionsMetaView

core_router = DefaultRouter()
core_router.register('audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.ventes.urls')),
    path('api/', include('apps.accounts.urls')),
    path('api/', include(core_router.urls)),
    path('api/meta/<str:resource>/', MetaView.as_view(), name='resource-meta'),
    path('api/permissions/', PermissionsMetaView.as_view(), name='permissions-meta'),
    path('api/token/', LoggingTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # OpenAPI schema (see SPECTACULAR_SETTINGS) — same schema `manage.py
    # spectacular --file schema.yml` writes to disk, exposed live too.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
]
