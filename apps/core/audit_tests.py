import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.core.models import AuditLog
from apps.ventes.factories import CustomerFactory, VenteFactory, VenteLigneFactory

pytestmark = pytest.mark.django_db

User = get_user_model()


def client_with_role(role_name, username, password='pass1234'):
    user = User.objects.create_user(username=username, password=password)
    user.roles.add(Role.objects.get(name=role_name))
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


def test_create_via_api_is_logged_with_actor():
    client, user = client_with_role('editor', 'audit_creator')

    response = client.post(
        '/api/customers/', {'name': 'Acme Corp', 'email': 'contact@acme.test'}, format='json'
    )

    assert response.status_code == 201, response.data
    log = AuditLog.objects.get(action='create', entity_type='accounts.customer')
    assert log.entity_id == response.data['id']
    assert log.actor_id == user.id
    assert log.actor_username == user.username


def test_update_via_api_logs_the_field_diff():
    client, _ = client_with_role('editor', 'audit_updater')
    customer = CustomerFactory(city='Paris')

    response = client.patch(f'/api/customers/{customer.id}/', {'city': 'Lyon'}, format='json')

    assert response.status_code == 200, response.data
    log = AuditLog.objects.get(
        action='update', entity_type='accounts.customer', entity_id=customer.id
    )
    assert log.changes['city'] == {'old': 'Paris', 'new': 'Lyon'}
    assert 'name' not in log.changes  # champ non modifié -> pas dans le diff


def test_delete_via_api_is_logged():
    client, _ = client_with_role('admin', 'audit_deleter')
    customer = CustomerFactory()

    response = client.delete(f'/api/customers/{customer.id}/')

    assert response.status_code == 204
    assert AuditLog.objects.filter(
        action='delete', entity_type='accounts.customer', entity_id=customer.id
    ).exists()


def test_objects_created_outside_a_request_are_not_logged():
    AuditLog.objects.all().delete()

    VenteFactory()

    assert not AuditLog.objects.exists()


def test_workflow_transition_logs_a_dedicated_entry_in_addition_to_the_status_diff():
    client, user = client_with_role('achat', 'audit_workflow')
    vente = VenteFactory()
    VenteLigneFactory(vente=vente)

    response = client.post(f'/api/ventes/{vente.id}/transition/valider_achat/')

    assert response.status_code == 200, response.data
    workflow_log = AuditLog.objects.get(
        action='workflow', entity_type='ventes.vente', entity_id=vente.id
    )
    assert workflow_log.action_name == 'valider_achat'
    assert workflow_log.actor_id == user.id
    status_logs = [
        log
        for log in AuditLog.objects.filter(
            action='update', entity_type='ventes.vente', entity_id=vente.id
        )
        if 'status' in log.changes
    ]
    assert len(status_logs) == 1
    assert status_logs[0].changes['status'] == {'old': '1', 'new': '3'}


def test_login_is_logged_but_login_failed_is_not():
    user = User.objects.create_user(username='audit_login', password='pass1234')
    client = APIClient()

    ok = client.post(
        '/api/token/', {'username': 'audit_login', 'password': 'pass1234'}, format='json'
    )
    bad = client.post(
        '/api/token/', {'username': 'audit_login', 'password': 'wrong'}, format='json'
    )

    assert ok.status_code == 200
    assert bad.status_code == 401
    assert AuditLog.objects.filter(action='login', entity_id=user.id).count() == 1


def test_audit_log_read_requires_permission():
    client, _ = client_with_role('user', 'audit_reader')
    admin_client, _ = client_with_role('admin', 'audit_admin_reader')
    CustomerFactory()  # produit au moins une entrée à lire

    denied = client.get('/api/audit-logs/')
    allowed = admin_client.get('/api/audit-logs/')

    assert denied.status_code == 403
    assert allowed.status_code == 200
