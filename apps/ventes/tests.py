from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.ventes.factories import (
    BonCommandeFactory,
    BonCommandeLigneFactory,
    CustomerFactory,
    FournisseurFactory,
    LivraisonFactory,
    ProductFactory,
    VenteFactory,
    VenteLigneFactory,
)
from apps.ventes.models import Vente, VenteStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    user = get_user_model().objects.create_user(username='alice', password='pass1234')
    user.roles.add(Role.objects.get(name='editor'))
    return user


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def client_with_role(role_name, username):
    user = get_user_model().objects.create_user(username=username, password='pass1234')
    user.roles.add(Role.objects.get(name=role_name))
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


def test_create_vente_with_lines_recalculates_total(api_client):
    customer = CustomerFactory()
    product = ProductFactory(default_price=20)

    payload = {
        'customer': customer.id,
        'lines': [
            {'product': product.id, 'quantity': '2', 'unit_price': '20.00', 'tva_rate': '0'},
            {'product': product.id, 'quantity': '1', 'unit_price': '5.00', 'tva_rate': '0'},
        ],
    }

    response = api_client.post('/api/ventes/', payload, format='json')

    assert response.status_code == 201, response.data
    vente = Vente.objects.get(id=response.data['id'])
    assert vente.total == 45
    assert vente.lines.count() == 2


def test_signal_recalculates_total_on_line_delete():
    vente = VenteFactory()
    line1 = VenteLigneFactory(vente=vente, quantity=2, unit_price=10, tva_rate=0)
    VenteLigneFactory(vente=vente, quantity=1, unit_price=5, tva_rate=0)
    vente.refresh_from_db()
    assert vente.total == 25

    line1.delete()
    vente.refresh_from_db()
    assert vente.total == 5


def test_transition_unknown_step_returns_404(api_client):
    vente = VenteFactory()

    response = api_client.post(f'/api/ventes/{vente.id}/transition/not-a-step/')

    assert response.status_code == 404


def test_valider_achat_requires_permission():
    client, _ = client_with_role('user', 'no_achat_perm')
    vente = VenteFactory(status=VenteStatus.CREE)

    response = client.post(f'/api/ventes/{vente.id}/transition/valider_achat/')

    assert response.status_code == 403
    vente.refresh_from_db()
    assert vente.status == VenteStatus.CREE


def test_valider_achat_success():
    client, _ = client_with_role('achat', 'achat_user')
    vente = VenteFactory(status=VenteStatus.CREE)

    response = client.post(f'/api/ventes/{vente.id}/transition/valider_achat/')

    assert response.status_code == 200, response.data
    vente.refresh_from_db()
    assert vente.status == VenteStatus.VALIDE_ACHAT


def test_valider_caisse_can_skip_achat():
    client, _ = client_with_role('caisse', 'caisse_user')
    vente = VenteFactory(status=VenteStatus.CREE)

    response = client.post(f'/api/ventes/{vente.id}/transition/valider_caisse/')

    assert response.status_code == 200, response.data
    vente.refresh_from_db()
    assert vente.status == VenteStatus.VALIDE_CAISSE


def test_achat_cannot_validate_after_caisse_has():
    client, _ = client_with_role('achat', 'achat_after_caisse')
    vente = VenteFactory(status=VenteStatus.VALIDE_CAISSE)

    response = client.post(f'/api/ventes/{vente.id}/transition/valider_achat/')

    assert response.status_code == 400
    vente.refresh_from_db()
    assert vente.status == VenteStatus.VALIDE_CAISSE


def test_rejeter_achat_is_terminal():
    client, _ = client_with_role('achat', 'achat_rejects')
    vente = VenteFactory(status=VenteStatus.CREE)

    response = client.post(f'/api/ventes/{vente.id}/transition/rejeter_achat/')
    assert response.status_code == 200, response.data
    vente.refresh_from_db()
    assert vente.status == VenteStatus.REJETEE_ACHAT

    caisse_client, _ = client_with_role('caisse', 'caisse_after_reject')
    response = caisse_client.post(f'/api/ventes/{vente.id}/transition/valider_caisse/')
    assert response.status_code == 400


def test_valider_dg_creates_livraison():
    client, _ = client_with_role('dg', 'dg_user')
    vente = VenteFactory(status=VenteStatus.VALIDE_CAISSE)

    response = client.post(f'/api/ventes/{vente.id}/transition/valider_dg/')

    assert response.status_code == 200, response.data
    vente.refresh_from_db()
    assert vente.status == VenteStatus.VALIDE_DG
    assert vente.livraisons.count() == 1


def test_dg_role_inherits_achat_and_caisse_permissions():
    # Hiérarchie : dg peut valider à n'importe quel niveau, pas seulement
    # le sien — pas besoin de passer par achat/caisse d'abord.
    client, _ = client_with_role('dg', 'dg_inherits')
    vente = VenteFactory(status=VenteStatus.CREE)

    response = client.post(f'/api/ventes/{vente.id}/transition/valider_achat/')
    assert response.status_code == 200, response.data
    vente.refresh_from_db()
    assert vente.status == VenteStatus.VALIDE_ACHAT

    response = client.post(f'/api/ventes/{vente.id}/transition/valider_caisse/')
    assert response.status_code == 200, response.data
    vente.refresh_from_db()
    assert vente.status == VenteStatus.VALIDE_CAISSE


def test_allowed_steps_reflects_status_and_permissions():
    vente = VenteFactory(status=VenteStatus.CREE)
    achat_client, _ = client_with_role('achat', 'achat_allowed')
    dg_client, _ = client_with_role('dg', 'dg_allowed')

    achat_response = achat_client.get(f'/api/ventes/{vente.id}/allowed-steps/')
    dg_response = dg_client.get(f'/api/ventes/{vente.id}/allowed-steps/')

    assert achat_response.status_code == 200
    assert set(achat_response.data['allowed_steps']) == {
        'valider_achat', 'rejeter_achat', 'annuler'
    }
    assert dg_response.status_code == 200
    # dg hérite d'achat et de caisse (voir la migration de seed) : il peut
    # jouer n'importe quelle étape depuis le brouillon, pas seulement la
    # sienne.
    assert set(dg_response.data['allowed_steps']) == {
        'valider_achat', 'rejeter_achat',
        'valider_caisse', 'rejeter_caisse',
        'valider_dg', 'rejeter_dg',
        'annuler',
    }


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


def test_annuler_requires_draft_status():
    client, _ = client_with_role('admin', 'admin_cancels')
    vente = VenteFactory(status=VenteStatus.VALIDE_DG)

    response = client.post(f'/api/ventes/{vente.id}/transition/annuler/')

    assert response.status_code == 400


def test_annuler_success():
    client, _ = client_with_role('admin', 'admin_cancels_draft')
    vente = VenteFactory(status=VenteStatus.CREE)

    response = client.post(f'/api/ventes/{vente.id}/transition/annuler/')

    assert response.status_code == 200
    vente.refresh_from_db()
    assert vente.status == VenteStatus.ANNULEE


def test_line_and_global_discount_are_applied_to_total():
    vente = VenteFactory(discount_percent=10)
    # (2 * 20) * 0.9 [remise ligne] = 36 ; puis * 0.9 [remise globale] = 32.40 (pas de TVA ici)
    VenteLigneFactory(vente=vente, quantity=2, unit_price=20, discount_percent=10, tva_rate=0)
    vente.refresh_from_db()
    assert vente.subtotal_ht == Decimal('36.00')
    assert vente.discount_amount == Decimal('3.60')
    assert vente.tva_amount == Decimal('0.00')
    assert vente.total == Decimal('32.40')


def test_tva_is_applied_after_discounts():
    vente = VenteFactory(discount_percent=10)
    # HT ligne = 100 ; remise globale 10% -> net HT = 90 ; TVA 20% de 90 = 18 ; total = 108
    VenteLigneFactory(vente=vente, quantity=1, unit_price=100, discount_percent=0, tva_rate=20)
    vente.refresh_from_db()
    assert vente.subtotal_ht == Decimal('100.00')
    assert vente.tva_amount == Decimal('18.00')
    assert vente.total == Decimal('108.00')


def test_update_vente_discount_without_touching_lines_recalculates_total(api_client):
    vente = VenteFactory(discount_percent=0)
    VenteLigneFactory(vente=vente, quantity=1, unit_price=100, tva_rate=0)
    vente.refresh_from_db()
    assert vente.total == 100

    response = api_client.patch(
        f'/api/ventes/{vente.id}/', {'discount_percent': '20'}, format='json'
    )

    assert response.status_code == 200, response.data
    vente.refresh_from_db()
    assert vente.total == 80


def test_livraison_list_filtered_by_vente(api_client):
    vente = VenteFactory()
    LivraisonFactory(vente=vente)
    LivraisonFactory()  # attached to a different vente

    response = api_client.get(f'/api/livraisons/?vente={vente.id}')

    assert response.status_code == 200, response.data
    assert response.data['count'] == 1


def test_paiement_create(api_client):
    vente = VenteFactory()

    response = api_client.post(
        '/api/paiements/',
        {'vente': vente.id, 'amount': '50.00', 'method': 'card'},
        format='json',
    )

    assert response.status_code == 201, response.data
    assert vente.paiements.count() == 1


def test_fournisseur_create_and_list(api_client):
    response = api_client.post(
        '/api/fournisseurs/',
        {'name': 'Acme Supplies', 'email': 'contact@acme-supplies.test', 'is_active': True},
        format='json',
    )
    assert response.status_code == 201, response.data
    assert response.data['id'].startswith('FRN')

    response = api_client.get('/api/fournisseurs/')
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_fournisseur_requires_authentication():
    client = APIClient()
    response = client.get('/api/fournisseurs/')
    assert response.status_code == 401


def test_fournisseur_role_without_permission_is_forbidden():
    role_without_access = Role.objects.create(id='ROL09999', name='no-access')
    user = get_user_model().objects.create_user(username='bob', password='pass1234')
    user.roles.add(role_without_access)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/fournisseurs/')

    assert response.status_code == 403


def test_user_role_cannot_delete_fournisseur():
    fournisseur = FournisseurFactory()
    user = get_user_model().objects.create_user(username='carla', password='pass1234')
    user.roles.add(Role.objects.get(name='user'))
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.delete(f'/api/fournisseurs/{fournisseur.id}/')

    assert response.status_code == 403


def test_annuler_requires_cancel_permission():
    client, _ = client_with_role('user', 'readonly')  # 'user' n'a pas cancel_vente
    vente = VenteFactory(status=VenteStatus.CREE)

    response = client.post(f'/api/ventes/{vente.id}/transition/annuler/')

    assert response.status_code == 403


def test_create_fournisseur(api_client):
    payload = {'name': 'Grossiste SARL', 'email': 'contact@grossiste.test', 'is_active': True}

    response = api_client.post('/api/fournisseurs/', payload, format='json')

    assert response.status_code == 201, response.data
    assert response.data['name'] == 'Grossiste SARL'
    assert response.data['is_active'] is True


def test_list_fournisseurs(api_client):
    FournisseurFactory.create_batch(3)

    response = api_client.get('/api/fournisseurs/')

    assert response.status_code == 200
    assert response.data['count'] == 3


def test_fournisseur_delete_requires_delete_permission():
    user_role_holder = get_user_model().objects.create_user(
        username='fournisseur_user', password='pass1234'
    )
    user_role_holder.roles.add(Role.objects.get(name='user'))
    client = APIClient()
    client.force_authenticate(user=user_role_holder)
    fournisseur = FournisseurFactory()

    response = client.delete(f'/api/fournisseurs/{fournisseur.id}/')

    assert response.status_code == 403


def test_fournisseur_delete_allowed_for_admin():
    admin_user = get_user_model().objects.create_user(
        username='fournisseur_admin', password='pass1234'
    )
    admin_user.roles.add(Role.objects.get(name='admin'))
    client = APIClient()
    client.force_authenticate(user=admin_user)
    fournisseur = FournisseurFactory()

    response = client.delete(f'/api/fournisseurs/{fournisseur.id}/')

    assert response.status_code == 204


def test_to_vente_defaults_returns_shaped_payload(api_client):
    bon = BonCommandeFactory(currency='EUR', discount_percent=Decimal('5'))
    BonCommandeLigneFactory(bon_commande=bon, quantity=Decimal('2'), unit_price=Decimal('15.00'))

    response = api_client.get(f'/api/bons-commande/{bon.id}/to_vente_defaults/')

    assert response.status_code == 200
    assert response.data['customer'] == bon.customer_id
    assert response.data['currency'] == 'EUR'
    assert len(response.data['lines']) == 1
    assert response.data['lines'][0]['quantity'] == Decimal('2')


def test_bon_commande_list_and_retrieve_expose_resolved_labels(api_client):
    bon = BonCommandeFactory()
    line = BonCommandeLigneFactory(bon_commande=bon)

    listed = api_client.get('/api/bons-commande/')
    retrieved = api_client.get(f'/api/bons-commande/{bon.id}/')

    assert listed.status_code == 200
    row = next(r for r in listed.data['results'] if r['id'] == bon.id)
    assert row['customer_name'] == bon.customer.name
    assert row['lines'][0]['product_name'] == line.product.name
    assert row['lines'][0]['product_sku'] == line.product.sku
    assert retrieved.status_code == 200
    assert retrieved.data['customer_name'] == bon.customer.name
