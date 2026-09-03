from django.apps import AppConfig


class VentesConfig(AppConfig):
    name = 'apps.ventes'

    def ready(self):
        from apps.ventes import signals  # noqa: F401
