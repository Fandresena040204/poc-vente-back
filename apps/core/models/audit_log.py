from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Journal d'ajout seul : connexions, créations, modifications,
    suppressions, et actions de workflow (voir apps/accounts/workflow.py).
    Pas d'API d'écriture ni de suppression (apps/core/views.py expose un
    `ReadOnlyModelViewSet`) — aucun code applicatif ne doit faire
    `AuditLog.objects.filter(...).update()`/`.delete()`.

    Volontairement absent : les tentatives refusées (403), les lectures
    (GET), les échecs de connexion, l'IP et le user-agent — décision prise
    avec l'équipe, pas une limite technique."""

    ACTION_CHOICES = [
        ('login', 'Connexion'),
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
        ('workflow', 'Action de workflow'),
    ]

    occurred_at = models.DateTimeField(auto_now_add=True)
    # FK nullable + nom figé : l'entrée reste lisible même si le compte est
    # supprimé ensuite.
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    actor_username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    # Nom de l'étape de workflow jouée (ex. 'valider_dg'), vide sinon.
    action_name = models.CharField(max_length=100, blank=True)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=50, blank=True)
    # {champ: {"old": ..., "new": ...}} — champs modifiés seulement.
    changes = models.JSONField(default=dict, blank=True)
    result = models.CharField(max_length=10, default='ok')
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'audit_log'
        ordering = ['-occurred_at']

    def __str__(self):
        return f'{self.action} {self.entity_type}#{self.entity_id}'
