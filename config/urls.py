from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views import defaults
from drf_spectacular.views import SpectacularAPIView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoggingTokenObtainPairView
from apps.core.errors import DEFAULT_MESSAGES, ErrorCode
from apps.core.views import AuditLogViewSet, MetaView, PermissionsMetaView

core_router = DefaultRouter()
core_router.register('audit-logs', AuditLogViewSet, basename='auditlog')



def _api_error(code, status):
    body = {'code': code, 'message': DEFAULT_MESSAGES[code], 'champs': {}}
    return JsonResponse(body, status=status)


def _api_catch_all(request):
    """URL `/api/...` inconnue → 404 au format commun, même en `DEBUG`
    (Django n'appelle `handler404` qu'avec `DEBUG=False`)."""
    return _api_error(ErrorCode.NOT_FOUND, 404)


def handler404(request, exception=None):
    if request.path.startswith('/api/'):
        return _api_error(ErrorCode.NOT_FOUND, 404)
    return defaults.page_not_found(request, exception)


def handler500(request):
    # Exception levée hors d'une vue DRF (middleware...) : les vues DRF
    # passent déjà par `apps.core.exception_handler`.
    if request.path.startswith('/api/'):
        return _api_error(ErrorCode.SERVER_ERROR, 500)
    return defaults.server_error(request)


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
    # En dernier : n'attrape que ce qu'aucune route `/api/` n'a pris.
    re_path(r'^api/', _api_catch_all),
]
