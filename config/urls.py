from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.core.views import MetaView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.ventes.urls')),
    path('api/meta/<str:resource>/', MetaView.as_view(), name='resource-meta'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
