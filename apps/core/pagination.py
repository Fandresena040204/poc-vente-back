from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """Pagination par défaut de l'API : permet au client de choisir
    `page_size` (ex: le sélecteur de taille de page du frontend), plafonné
    pour éviter qu'un client ne demande une page arbitrairement grande."""

    page_size_query_param = 'page_size'
    max_page_size = 100
