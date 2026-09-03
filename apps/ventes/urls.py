from rest_framework.routers import DefaultRouter

from apps.ventes.views import ProductViewSet, VenteViewSet

router = DefaultRouter()
router.register('ventes', VenteViewSet, basename='vente')
router.register('products', ProductViewSet, basename='product')

urlpatterns = router.urls
