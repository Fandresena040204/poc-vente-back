import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.ventes.factories import VenteFactory, VenteLigneFactory

pytestmark = pytest.mark.django_db

User = get_user_model()


def client_with_role(role_name, username, password='pass1234'):
    user = User.objects.create_user(username=username, password=password)
    user.roles.add(Role.objects.get(name=role_name))
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


def test_history_returns_only_this_entity_entries():
    """`GET /api/ventes/{id}/history/` ne renvoie que les entrées de cette vente,
    dans l'ordre décroissant, avec la forme paginée standard."""
    client, _ = client_with_role('admin', 'hist_admin')
    vente1 = VenteFactory()
    vente2 = VenteFactory()
    VenteLigneFactory(vente=vente1)
    VenteLigneFactory(vente=vente2)

    # Crée des entrées d'audit pour les deux ventes via l'API
    client.post(f'/api/ventes/{vente1.id}/transition/valider_achat/')
    client.post(f'/api/ventes/{vente2.id}/transition/valider_achat/')

    # Historique de vente1
    response = client.get(f'/api/ventes/{vente1.id}/history/')
    assert response.status_code == 200, response.data
    data = response.data
    assert 'results' in data
    assert 'count' in data
    assert data['count'] >= 1
    for entry in data['results']:
        assert entry['entity_id'] == str(vente1.id)
    # Ordre décroissant
    dates = [entry['occurred_at'] for entry in data['results']]
    assert dates == sorted(dates, reverse=True)


def test_history_403_without_view_vente():
    """Un utilisateur sans `view_vente` reçoit 403 `permission_denied`."""
    User = get_user_model()
    user = User.objects.create_user(username='hist_no_view', password='pass1234')
    # Pas de rôle -> pas de permission view_vente
    client = APIClient()
    client.force_authenticate(user=user)
    vente = VenteFactory()
    VenteLigneFactory(vente=vente)

    response = client.get(f'/api/ventes/{vente.id}/history/')
    assert response.status_code == 403
    assert response.data['code'] == 'permission_denied'


def test_history_404_for_nonexistent_id():
    """ID inexistant -> 404 `not_found`."""
    client, _ = client_with_role('admin', 'hist_404')
    response = client.get('/api/ventes/999999/history/')
    assert response.status_code == 404
    assert response.data['code'] == 'not_found'


def test_history_accessible_with_view_vente_even_without_view_auditlog():
    """Un utilisateur caisse (qui a `view_vente` mais pas `view_auditlog`)
    peut accéder à l'historique de sa vente."""
    client, _ = client_with_role('caisse', 'hist_caisse')
    vente = VenteFactory()
    VenteLigneFactory(vente=vente)

    client.post(f'/api/ventes/{vente.id}/transition/valider_caisse/')

    response = client.get(f'/api/ventes/{vente.id}/history/')
    assert response.status_code == 200, response.data
    assert response.data['count'] >= 1
    for entry in response.data['results']:
        assert entry['entity_id'] == str(vente.id)


def test_history_pagination():
    """La réponse est paginée avec `page_size` configurable."""
    client, _ = client_with_role('admin', 'hist_page')
    vente = VenteFactory()
    VenteLigneFactory(vente=vente)

    # Crée plusieurs entrées
    for _ in range(3):
        vente.status = 1
        vente.save()
        client.post(f'/api/ventes/{vente.id}/transition/valider_achat/')
        # Remet en arrière pour rejouer (via update direct pour le test)
        vente.status = 1
        vente.save(update_fields=['status'])

    response = client.get(f'/api/ventes/{vente.id}/history/?page_size=2')
    assert response.status_code == 200
    data = response.data
    assert 'results' in data
    assert len(data['results']) <= 2
    assert 'next' in data
    assert 'previous' in data