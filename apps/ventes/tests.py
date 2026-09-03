import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.ventes.factories import CustomerFactory, ProductFactory, VenteFactory, VenteLigneFactory
from apps.ventes.models import Vente, VenteStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username='alice', password='pass1234')


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_create_vente_with_lines_recalculates_total(api_client):
    customer = CustomerFactory()
    product = ProductFactory(default_price=20)

    payload = {
        'customer': customer.id,
        'lines': [
            {'product': product.id, 'quantity': '2', 'unit_price': '20.00'},
            {'product': product.id, 'quantity': '1', 'unit_price': '5.00'},
        ],
    }

    response = api_client.post('/api/ventes/', payload, format='json')

    assert response.status_code == 201, response.data
    vente = Vente.objects.get(id=response.data['id'])
    assert vente.total == 45
    assert vente.lines.count() == 2


def test_signal_recalculates_total_on_line_delete():
    vente = VenteFactory()
    line1 = VenteLigneFactory(vente=vente, quantity=2, unit_price=10)
    VenteLigneFactory(vente=vente, quantity=1, unit_price=5)
    vente.refresh_from_db()
    assert vente.total == 25

    line1.delete()
    vente.refresh_from_db()
    assert vente.total == 5


def test_valider_action_requires_draft_status(api_client):
    vente = VenteFactory(status=VenteStatus.VALIDATED)

    response = api_client.post(f'/api/ventes/{vente.id}/valider/')

    assert response.status_code == 400


def test_valider_action_success(api_client):
    vente = VenteFactory(status=VenteStatus.DRAFT)

    response = api_client.post(f'/api/ventes/{vente.id}/valider/')

    assert response.status_code == 200
    vente.refresh_from_db()
    assert vente.status == VenteStatus.VALIDATED


def test_vente_list_has_no_n_plus_one_queries(api_client):
    for _ in range(5):
        vente = VenteFactory()
        VenteLigneFactory.create_batch(2, vente=vente)

    with CaptureQueriesContext(connection) as ctx:
        response = api_client.get('/api/ventes/')
    assert response.status_code == 200

    query_count_5 = len(ctx.captured_queries)

    extra_vente = VenteFactory()
    VenteLigneFactory.create_batch(2, vente=extra_vente)

    with CaptureQueriesContext(connection) as ctx:
        response = api_client.get('/api/ventes/')
    assert response.status_code == 200

    query_count_6 = len(ctx.captured_queries)

    assert query_count_6 == query_count_5


def test_unauthenticated_request_is_rejected():
    client = APIClient()
    response = client.get('/api/ventes/')
    assert response.status_code == 401
