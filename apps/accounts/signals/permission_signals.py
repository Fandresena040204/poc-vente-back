from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_custom_permissions(sender, app_config, **kwargs):
    # Convention du projet (guide backend § 0) : toute app métier est
    # enregistrée sous "apps.<nom>" — jamais les apps tierces
    # (rest_framework, django.contrib.*...). Une nouvelle app métier est
    # donc reconnue automatiquement, sans liste à étendre ici.
    if not app_config.name.startswith('apps.'):
        return

    from apps.accounts.models import Permission

    for model in app_config.get_models():
        # Les modèles unmanaged (vues DB de lecture, ex. VenteListView) n'ont
        # pas leurs propres permissions : les actions se vérifient toujours
        # sur le modèle réel (`view_vente`, pas `view_ventelistview`).
        if not model._meta.managed:
            continue
        for action in model._meta.default_permissions:
            codename = f'{action}_{model._meta.model_name}'
            Permission.objects.get_or_create(
                app_label=app_config.label,
                model=model._meta.model_name,
                codename=codename,
                defaults={'name': f'Can {action} {model._meta.verbose_name}'},
            )
