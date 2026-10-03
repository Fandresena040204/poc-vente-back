from apps.ventes.signals import vente_ligne_signals  # noqa: F401

# Un fichier par modèle émetteur (même convention que models/serializers/
# views/admin/filters) — chaque nouveau signal ajoute son propre
# <entite>_signals.py, importé ici pour être enregistré au démarrage de
# l'app (voir apps/ventes/apps.py, AppConfig.ready()).
