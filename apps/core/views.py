from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import CustomerSerializer
from apps.ventes.serializers import ProductSerializer, VenteSerializer

RESOURCE_SERIALIZER_MAP = {
    'ventes': VenteSerializer,
    'products': ProductSerializer,
    'customers': CustomerSerializer,
}


class MetaView(APIView):
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
