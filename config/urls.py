from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.core.views import MetaView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.ventes.urls')),
    path('api/', include('apps.accounts.urls')),
    path('api/meta/<str:resource>/', MetaView.as_view(), name='resource-meta'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # OpenAPI schema (see SPECTACULAR_SETTINGS) — same schema `manage.py
    # spectacular --file schema.yml` writes to disk, exposed live too.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
]
