from rest_framework.routers import DefaultRouter

from apps.ventes.views import FournisseurViewSet, ProductViewSet, VenteViewSet

router = DefaultRouter()
router.register('ventes', VenteViewSet, basename='vente')
router.register('products', ProductViewSet, basename='product')
router.register('fournisseurs', FournisseurViewSet, basename='fournisseur')

urlpatterns = router.urls
