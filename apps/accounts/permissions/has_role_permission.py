from rest_framework.permissions import BasePermission

from apps.accounts.models import UserPermissionOverride

ACTION_TO_PERMISSION = {
    'list': 'view',
    'retrieve': 'view',
    'create': 'add',
    'update': 'change',
    'partial_update': 'change',
    'destroy': 'delete',
}


class HasRolePermission(BasePermission):
    message = "Aucun de vos roles ne dispose de la permission requise."
    default_custom_action_permission = 'change'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        action = ACTION_TO_PERMISSION.get(view.action, self.default_custom_action_permission)
        model = view.serializer_class.Meta.model
        if not self._has_codename(user, model, f'{action}_{model._meta.model_name}'):
            return False
        # A write must also be readable: without `view`, a change would still
        # succeed on an entity the user is not allowed to see.
        return action == 'view' or self._has_codename(user, model, f'view_{model._meta.model_name}')

    @staticmethod
    def _has_codename(user, model, codename):
        """`codename` is the full permission codename (ex. 'change_vente',
        'validate_achat_vente') — never just the short action verb."""
        override = UserPermissionOverride.objects.filter(
            user=user,
            permission__codename=codename,
            permission__app_label=model._meta.app_label,
        ).first()
        if override is not None:
            return override.is_allowed

        return user.roles.filter(
            permissions__codename=codename,
            permissions__app_label=model._meta.app_label,
        ).exists()

    @staticmethod
    def effective_codenames(user, model):
        """Tous les codenames effectivement accordés à `user` pour `model`
        (rôles, avec les exceptions appliquées) — deux requêtes au total,
        quel que soit le nombre de codenames à vérifier ensuite. À utiliser
        quand on doit vérifier plusieurs permissions pour le même
        utilisateur/modèle (ex. une ligne de liste) : appeler
        `_has_codename` en boucle ferait une requête par codename et par
        ligne (N+1)."""
        overrides = dict(
            UserPermissionOverride.objects.filter(
                user=user, permission__app_label=model._meta.app_label
            ).values_list('permission__codename', 'is_allowed')
        )
        role_codenames = set(
            user.roles.filter(permissions__app_label=model._meta.app_label).values_list(
                'permissions__codename', flat=True
            )
        )
        candidates = role_codenames | overrides.keys()
        return {c for c in candidates if overrides.get(c, c in role_codenames)}
