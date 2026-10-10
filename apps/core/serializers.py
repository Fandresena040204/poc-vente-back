from rest_framework import serializers

from apps.core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id', 'occurred_at', 'actor', 'actor_username', 'action', 'action_name',
            'entity_type', 'entity_id', 'changes', 'result', 'method', 'path',
        ]
