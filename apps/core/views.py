from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Permission
from apps.accounts.permissions import IsAdminRole
from apps.accounts.serializers import CustomerSerializer
from apps.ventes.serializers import (
    LivraisonSerializer,
    PaiementSerializer,
    ProductCategorySerializer,
    ProductSerializer,
    VenteSerializer,
)

RESOURCE_SERIALIZER_MAP = {
    'ventes': VenteSerializer,
    'products': ProductSerializer,
    'product-categories': ProductCategorySerializer,
    'customers': CustomerSerializer,
    'livraisons': LivraisonSerializer,
    'paiements': PaiementSerializer,
}


class MetaView(APIView):
    # Excluded from the generated OpenAPI schema: its response shape
    # depends on `resource` at runtime (introspects whichever serializer
    # RESOURCE_SERIALIZER_MAP maps it to), which doesn't fit a fixed
    # schema — and it's metadata, not an entity, so pagekit-showcase's
    # generated types don't need it anyway.
    @extend_schema(exclude=True)
    def get(self, request, resource):
        serializer_class = RESOURCE_SERIALIZER_MAP.get(resource)
        if serializer_class is None:
            return Response({'detail': 'Ressource inconnue.'}, status=404)

        fields_meta = []
        for name, field in serializer_class().fields.items():
            fields_meta.append({
                'name': name,
                'type': field.__class__.__name__,
                'required': field.required,
                'read_only': field.read_only,
                'label': field.label,
                'choices': getattr(field, 'choices', None),
            })
        return Response({'resource': resource, 'fields': fields_meta})


class PermissionsMetaView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(responses=inline_serializer(
        name='PermissionGroup',
        fields={
            'app_label': serializers.CharField(),
            'model': serializers.CharField(),
            'codenames': serializers.ListField(child=serializers.CharField()),
        },
        many=True,
    ))
    def get(self, request):
        permissions = Permission.objects.all().order_by('app_label', 'model')
        grouped = {}
        for p in permissions:
            key = (p.app_label, p.model)
            grouped.setdefault(key, []).append(p.codename)
        return Response([
            {'app_label': app, 'model': model, 'codenames': codenames}
            for (app, model), codenames in grouped.items()
        ])
