from apps.accounts.signals import permission_signals  # noqa: F401

# Un fichier par domaine de signal (même convention que apps/ventes/signals/)
# — connecté une seule fois ici (l'app "propriétaire" de Permission), mais
# se déclenche pour chaque app après migrate car il se filtre lui-même sur
# app_config.name (voir permission_signals.py).
