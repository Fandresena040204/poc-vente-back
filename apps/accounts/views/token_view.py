from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.models import AuditLog


class LoggingTokenObtainPairView(TokenObtainPairView):
    """Même comportement que `TokenObtainPairView`, en plus d'une entrée
    `AuditLog` sur une connexion réussie — `login_failed` n'est volontairement
    pas journalisé (décision prise avec l'équipe)."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get('username', '')
            user = get_user_model().objects.filter(username=username).first()
            AuditLog.objects.create(
                actor=user,
                actor_username=username,
                action='login',
                entity_type='accounts.user',
                entity_id=user.id if user else '',
                method=request.method,
                path=request.path,
            )
        return response
