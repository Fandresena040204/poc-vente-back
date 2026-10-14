"""Tests pour le contrat d'erreur unifié.

Un test par code réellement produit : statut + code + présence de message et champs.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.core.errors import ErrorCode
from apps.core.exception_handler import api_exception_handler
from apps.ventes.factories import CustomerFactory, ProductFactory, VenteFactory
from apps.ventes.models import VenteStatus

pytestmark = pytest.mark.django_db

User = get_user_model()


def _handle(exc):
    return api_exception_handler(exc, {'view': None, 'request': None})


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client():
    """Client authentifié avec rôle editor (permissions de base)."""
    user = User.objects.create_user(username='testuser', password='pass1234')
    user.roles.add(Role.objects.get(name='editor'))
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def achat_client():
    """Client avec rôle achat."""
    user = User.objects.create_user(username='achat_user', password='pass1234')
    user.roles.add(Role.objects.get(name='achat'))
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client():
    """Client avec rôle admin."""
    user = User.objects.create_user(username='admin_user', password='pass1234')
    user.roles.add(Role.objects.get(name='admin'))
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class TestErrorFormat:
    """Tests de format communs à toutes les erreurs."""

    def assert_error_format(self, response, expected_code, expected_status):
        """Vérifie le format standard d'une réponse d'erreur."""
        assert response.status_code == expected_status, response.data
        assert 'code' in response.data
        assert 'message' in response.data
        assert 'champs' in response.data
        assert response.data['code'] == expected_code
        assert isinstance(response.data['message'], str)
        assert len(response.data['message']) > 0
        assert isinstance(response.data['champs'], dict)


class TestValidationError(TestErrorFormat):
    """Tests pour validation_error (400)."""

    def test_missing_required_field(self, authenticated_client):
        """Champ obligatoire manquant -> validation_error avec champ dans champs."""
        response = authenticated_client.post('/api/ventes/', {}, format='json')
        self.assert_error_format(response, ErrorCode.VALIDATION_ERROR, status.HTTP_400_BAD_REQUEST)
        assert 'customer' in response.data['champs']

    def test_nested_error_on_vente_line(self, authenticated_client):
        """Erreur imbriquée sur une ligne de vente -> clé lines[1].product."""
        customer = CustomerFactory()
        product = ProductFactory()
        # product inexistant dans la 2e ligne -> erreur de validation sur lines[1].product
        line1 = {'product': product.id, 'quantity': '1', 'unit_price': '10.00', 'tva_rate': '0'}
        line2 = {'product': 'PRM99999', 'quantity': '1', 'unit_price': '10.00', 'tva_rate': '0'}
        payload = {'customer': customer.id, 'lines': [line1, line2]}
        response = authenticated_client.post('/api/ventes/', payload, format='json')
        self.assert_error_format(response, ErrorCode.VALIDATION_ERROR, status.HTTP_400_BAD_REQUEST)
        # La notation TanStack Form pour lines[1].product
        assert 'lines[1].product' in response.data['champs']

    def test_non_field_errors_in_message(self):
        """`non_field_errors` → dans `message`, pas dans `champs`."""
        exc = ValidationError({'non_field_errors': ['Globale.'], 'customer': ['Requis.']})
        response = _handle(exc)
        assert response.data == {
            'code': ErrorCode.VALIDATION_ERROR,
            'message': 'Globale.',
            'champs': {'customer': ['Requis.']},
        }

    def test_root_list_goes_to_message(self):
        """`ValidationError` levée avec une liste (ex. dans `validate()`) → `message`."""
        response = _handle(ValidationError(['Une vente doit contenir au moins une ligne.']))
        assert response.data['message'] == 'Une vente doit contenir au moins une ligne.'
        assert response.data['champs'] == {}

    def test_list_field_errors_use_brackets(self):
        """Erreurs indexées d'un `ListField` (`{0: [...]}`) → `tags[0]`."""
        response = _handle(ValidationError({'tags': {0: ['Invalide.']}}))
        assert response.data['champs'] == {'tags[0]': ['Invalide.']}


class TestParseError(TestErrorFormat):
    """Tests pour parse_error (400)."""

    def test_invalid_json(self, authenticated_client):
        """JSON malformé -> parse_error."""
        response = authenticated_client.post(
            '/api/ventes/',
            data='{invalid json}',
            content_type='application/json'
        )
        self.assert_error_format(response, ErrorCode.PARSE_ERROR, status.HTTP_400_BAD_REQUEST)


class TestNotAuthenticated(TestErrorFormat):
    """Tests pour not_authenticated (401)."""

    def test_no_token(self, api_client):
        """Requête sans jeton -> not_authenticated."""
        response = api_client.get('/api/ventes/')
        self.assert_error_format(
            response, ErrorCode.NOT_AUTHENTICATED, status.HTTP_401_UNAUTHORIZED
        )


class TestTokenInvalid(TestErrorFormat):
    """Tests pour token_invalid (401)."""

    def test_invalid_token(self, api_client):
        """Jeton invalide -> token_invalid."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer xxx.invalid.token')
        response = api_client.get('/api/ventes/')
        self.assert_error_format(response, ErrorCode.TOKEN_INVALID, status.HTTP_401_UNAUTHORIZED)


class TestInvalidCredentials(TestErrorFormat):
    """Tests pour invalid_credentials (401)."""

    def test_bad_credentials_on_login(self, api_client):
        """Mauvais identifiants sur /api/token/ -> invalid_credentials."""
        response = api_client.post(
            '/api/token/',
            {'username': 'existant', 'password': 'wrong'},
            format='json',
        )
        self.assert_error_format(
            response, ErrorCode.INVALID_CREDENTIALS, status.HTTP_401_UNAUTHORIZED
        )


class TestPermissionDenied(TestErrorFormat):
    """Tests pour permission_denied (403)."""

    def test_missing_permission_on_workflow_step(self, achat_client):
        """Étape de workflow sans permission -> permission_denied."""
        # achat_client n'a pas le droit de faire valider_caisse
        vente = VenteFactory(status=VenteStatus.CREE)
        response = achat_client.post(f'/api/ventes/{vente.id}/transition/valider_caisse/')
        self.assert_error_format(response, ErrorCode.PERMISSION_DENIED, status.HTTP_403_FORBIDDEN)
        assert 'étape' in response.data['message'].lower()


class TestNotFound(TestErrorFormat):
    """Tests pour not_found (404)."""

    def test_unknown_resource(self, authenticated_client):
        """Ressource inconnue (ID inexistant) -> not_found."""
        response = authenticated_client.get('/api/ventes/ID_INEXISTANT/')
        self.assert_error_format(response, ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND)

    def test_unknown_api_path(self, authenticated_client):
        """URL /api/ inconnue -> not_found (JSON même en DEBUG)."""
        response = authenticated_client.get('/api/inexistante/')
        # JsonResponse n'a pas .data, utiliser .json()
        import json
        data = json.loads(response.content)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert data['code'] == ErrorCode.NOT_FOUND
        assert 'message' in data
        assert 'champs' in data


class TestUnknownStep(TestErrorFormat):
    """Tests pour unknown_step (404)."""

    def test_unknown_workflow_step(self, achat_client):
        """Étape de workflow absente de la déclaration -> unknown_step."""
        vente = VenteFactory(status=VenteStatus.CREE)
        response = achat_client.post(f'/api/ventes/{vente.id}/transition/etape_inconnue/')
        self.assert_error_format(response, ErrorCode.UNKNOWN_STEP, status.HTTP_404_NOT_FOUND)


class TestMethodNotAllowed(TestErrorFormat):
    """Tests pour method_not_allowed (405)."""

    def test_wrong_method(self, authenticated_client):
        """Méthode HTTP non autorisée -> method_not_allowed."""
        response = authenticated_client.patch('/api/ventes/')  # PATCH sur list non autorisé
        self.assert_error_format(
            response, ErrorCode.METHOD_NOT_ALLOWED, status.HTTP_405_METHOD_NOT_ALLOWED
        )


class TestInvalidTransition(TestErrorFormat):
    """Tests pour invalid_transition (409)."""

    def test_transition_from_wrong_status(self, achat_client):
        """Statut actuel hors du `from` de l'étape -> invalid_transition (409)."""
        vente = VenteFactory(status=VenteStatus.VALIDE_CAISSE)
        response = achat_client.post(f'/api/ventes/{vente.id}/transition/valider_achat/')
        self.assert_error_format(response, ErrorCode.INVALID_TRANSITION, status.HTTP_409_CONFLICT)

    def test_rejected_vente_cannot_transition(self, achat_client):
        """Vente rejetée ne peut plus faire de transitions -> invalid_transition."""
        vente = VenteFactory(status=VenteStatus.REJETEE_ACHAT)
        response = achat_client.post(f'/api/ventes/{vente.id}/transition/valider_achat/')
        self.assert_error_format(response, ErrorCode.INVALID_TRANSITION, status.HTTP_409_CONFLICT)


class TestThrottled(TestErrorFormat):
    """Tests pour throttled (429)."""

    def test_throttled_keeps_retry_after(self):
        """`Throttled` → 429 `throttled`, l'en-tête `Retry-After` posé par DRF est conservé."""
        response = _handle(Throttled(wait=30))
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.data['code'] == ErrorCode.THROTTLED
        assert response['Retry-After'] == '30'


class TestServerError(TestErrorFormat):
    """Tests pour server_error (500)."""

    def test_unhandled_exception_in_view(self, authenticated_client, monkeypatch):
        """Exception Python non prévue dans une vue DRF -> 500 server_error sans trace."""
        from apps.ventes.views.vente_viewset import VenteViewSet

        def failing_list(self, request, *args, **kwargs):
            raise RuntimeError('Erreur de test intentionnelle')

        monkeypatch.setattr(VenteViewSet, 'list', failing_list)

        response = authenticated_client.get('/api/ventes/')
        self.assert_error_format(
            response, ErrorCode.SERVER_ERROR, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        # Pas de trace dans le corps
        assert 'trace' not in str(response.data).lower()
        assert 'runtimeerror' not in str(response.data).lower()


class TestErrorCodeCoverage:
    """Vérifie que tous les codes renvoyés existent dans ErrorCode."""

    def test_all_returned_codes_exist_in_enum(self, authenticated_client, achat_client, api_client):
        """Chaque code renvoyé par le gestionnaire appartient à ErrorCode."""
        import json

        def get_code(response):
            if hasattr(response, 'data'):
                return response.data['code']
            return json.loads(response.content)['code']

        # Faire plusieurs requêtes qui déclenchent différents codes
        test_cases = [
            (lambda: api_client.get('/api/ventes/'), ErrorCode.NOT_AUTHENTICATED),
            (
                lambda: authenticated_client.post('/api/ventes/', {}, format='json'),
                ErrorCode.VALIDATION_ERROR,
            ),
            (
                lambda: api_client.post(
                    '/api/token/', {'username': 'x', 'password': 'y'}, format='json'
                ),
                ErrorCode.INVALID_CREDENTIALS,
            ),
            (lambda: api_client.get('/api/inexistante/'), ErrorCode.NOT_FOUND),
        ]

        for call, expected_code in test_cases:
            response = call()
            code = get_code(response)
            assert code in ErrorCode.__members__.values(), \
                f"Code {code} n'est pas dans ErrorCode"


class TestOpenAPISchema:
    """Vérifie que le schéma OpenAPI contient le composant ApiError."""

    def test_api_error_in_schema(self):
        """Le composant ApiError est présent dans le schéma généré."""
        from drf_spectacular.generators import SchemaGenerator

        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)
        components = schema.get('components', {}).get('schemas', {})
        assert 'ApiError' in components, f"ApiError non trouvé dans {list(components.keys())}"

        api_error = components['ApiError']
        # Le schéma peut être une référence ($ref) ou l'objet direct
        ref_key = '$ref'
        if ref_key in api_error:
            # Résoudre la référence
            ref_path = api_error[ref_key]
            schema_name = ref_path.split('/')[-1]
            api_error = components[schema_name]

        assert api_error['type'] == 'object'
        assert 'code' in api_error['properties']
        assert 'message' in api_error['properties']
        assert 'champs' in api_error['properties']
        # code peut être un objet direct ou une référence ($ref) vers un enum
        code_prop = api_error['properties']['code']
        if ref_key in code_prop:
            # C'est une référence vers un enum
            enum_ref = code_prop[ref_key]
            enum_name = enum_ref.split('/')[-1]
            enum_schema = components[enum_name]
            assert enum_schema['type'] == 'string'
            assert 'enum' in enum_schema
            enum_values = enum_schema['enum']
        else:
            # Objet direct
            assert code_prop['type'] == 'string'
            assert 'enum' in code_prop
            enum_values = code_prop['enum']
        
        for code in ErrorCode:
            assert code.value in enum_values, f"Code {code.value} manquant dans l'enum OpenAPI"