from django_filters import rest_framework as filters


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    """Valeur `?champ=a,b,c` -> lookup `__in`. Utilisé pour les filtres
    "popup à cases à cocher" du frontend (ex: statut de vente, rôles d'un
    utilisateur), envoyés comme une liste de valeurs séparées par des
    virgules plutôt qu'une valeur exacte unique."""
