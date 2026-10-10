"""Journal d'audit général : connecté à `pre_save`/`post_save`/`post_delete`
sans `sender=` (apps/core/apps.py:CoreConfig.ready) — il voit donc toutes
les sauvegardes et suppressions, et décide lui-même, via `_should_audit`,
lesquelles concernent une app métier du projet (même convention que
`create_custom_permissions`, apps/accounts/signals/permission_signals.py).

N'écrit jamais pour `AuditLog` lui-même (sinon boucle infinie), ni pour un
modèle non managé (vues de lecture, ex. VenteListView) ou hors de
`apps.*`. Ne s'active que dans le contexte d'une requête HTTP
(`get_current_request()` non `None`) : les migrations de seed (RunPython
qui créent des `Role`/`Permission`...) et les scripts de gestion
sauvegardent aussi des modèles `apps.*`, avant même que la table
`audit_log` existe — et ce ne sont de toute façon pas des actions
utilisateur à journaliser.
"""

from apps.core.middleware import get_current_request

SENSITIVE_FIELDS = {'password'}
EXCLUDED_MODELS = {('core', 'auditlog')}


def _is_business_app(app_label):
    from django.apps import apps as global_apps

    return any(
        c.label == app_label and c.name.startswith('apps.') for c in global_apps.get_app_configs()
    )


def _should_audit(sender):
    if get_current_request() is None:
        return False
    meta = sender._meta
    if not meta.managed:
        return False
    if (meta.app_label, meta.model_name) in EXCLUDED_MODELS:
        return False
    return _is_business_app(meta.app_label)


def _current_actor():
    request = get_current_request()
    if request is None:
        return None
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        return None
    return user


def _request_meta():
    request = get_current_request()
    if request is None:
        return '', ''
    return request.method, request.path


def _write(**fields):
    from apps.core.models import AuditLog

    actor = fields.pop('actor', None)
    method, path = _request_meta()
    AuditLog.objects.create(
        actor=actor,
        actor_username=getattr(actor, 'username', ''),
        method=method,
        path=path,
        **fields,
    )


def stash_old_values(sender, instance, **kwargs):
    """`pre_save` : prend un instantané des valeurs avant écriture, pour
    que `log_save` (post_save) puisse calculer un diff. Un objet neuf (pas
    encore en base) n'a pas d'ancien état."""
    if not _should_audit(sender):
        return
    if not instance.pk:
        instance._audit_old_values = None
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._audit_old_values = None
        return
    instance._audit_old_values = {f.attname: getattr(old, f.attname) for f in sender._meta.fields}


def log_save(sender, instance, created, **kwargs):
    if not _should_audit(sender):
        return

    entity_type = f'{sender._meta.app_label}.{sender._meta.model_name}'
    if created:
        _write(
            actor=_current_actor(), action='create', entity_type=entity_type,
            entity_id=str(instance.pk), changes={},
        )
        return

    old = getattr(instance, '_audit_old_values', None)
    if old is None:
        return
    changes = {}
    for field in sender._meta.fields:
        if field.name in SENSITIVE_FIELDS:
            continue
        new_value = getattr(instance, field.attname)
        old_value = old.get(field.attname)
        if old_value != new_value:
            changes[field.name] = {
                'old': None if old_value is None else str(old_value),
                'new': None if new_value is None else str(new_value),
            }
    if not changes:
        return  # sauvegarde sans changement réel — rien à journaliser
    _write(
        actor=_current_actor(), action='update', entity_type=entity_type,
        entity_id=str(instance.pk), changes=changes,
    )


def log_delete(sender, instance, **kwargs):
    if not _should_audit(sender):
        return
    entity_type = f'{sender._meta.app_label}.{sender._meta.model_name}'
    _write(
        actor=_current_actor(), action='delete', entity_type=entity_type,
        entity_id=str(instance.pk), changes={},
    )


def log_workflow_action(user, obj, action_name, result='ok'):
    """Appelé explicitement par `WorkflowMixin.transition`
    (apps/accounts/workflow.py) — une entrée dédiée par étape jouée, en plus
    du diff `update` que `log_save` écrit déjà pour le changement de
    `status`."""
    entity_type = f'{obj._meta.app_label}.{obj._meta.model_name}'
    _write(
        actor=user, action='workflow', action_name=action_name,
        entity_type=entity_type, entity_id=str(obj.pk), changes={}, result=result,
    )
