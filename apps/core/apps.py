from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save, pre_save


class CoreConfig(AppConfig):
    name = 'apps.core'

    def ready(self):
        from apps.core.audit import log_delete, log_save, stash_old_values

        # Pas de `sender=` : voit toutes les sauvegardes/suppressions, et
        # filtre lui-même lesquelles journaliser (apps.core.audit._should_audit).
        pre_save.connect(stash_old_values, dispatch_uid='audit_stash_old_values')
        post_save.connect(log_save, dispatch_uid='audit_log_save')
        post_delete.connect(log_delete, dispatch_uid='audit_log_delete')
