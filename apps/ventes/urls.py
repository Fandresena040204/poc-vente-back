from rest_framework.routers import DefaultRouter

from apps.ventes.views import (
    LivraisonViewSet,
    PaiementViewSet,
    ProductCategoryViewSet,
    ProductViewSet,
    VenteViewSet,
)

router = DefaultRouter()
router.register('ventes', VenteViewSet, basename='vente')
router.register('products', ProductViewSet, basename='product')
router.register('product-categories', ProductCategoryViewSet, basename='productcategory')
router.register('livraisons', LivraisonViewSet, basename='livraison')
router.register('paiements', PaiementViewSet, basename='paiement')

urlpatterns = router.urls
