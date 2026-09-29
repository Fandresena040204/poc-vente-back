from rest_framework import viewsets

from apps.accounts.permissions import HasRolePermission
from apps.ventes.models import Fournisseur
from apps.ventes.serializers import FournisseurSerializer


class FournisseurViewSet(viewsets.ModelViewSet):
    serializer_class = FournisseurSerializer
    queryset = Fournisseur.objects.all()
    permission_classes = [HasRolePermission]
    search_fields = ['name', 'email']
    ordering_fields = ['name', 'created_at']
