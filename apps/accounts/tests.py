import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.accounts.permissions import ADMIN_ROLE_NAME

pytestmark = pytest.mark.django_db

User = get_user_model()


def make_admin(user):
    role, _ = Role.objects.get_or_create(name=ADMIN_ROLE_NAME)
    user.roles.add(role)
    return user


def test_register_creates_user_and_returns_tokens():
    client = APIClient()
    payload = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'SuperSecret123!',
    }

    response = client.post('/api/auth/register/', payload, format='json')

    assert response.status_code == 201, response.data
    assert User.objects.filter(username='newuser').exists()
    assert 'access' in response.data
    assert 'refresh' in response.data


def test_register_rejects_weak_password():
    client = APIClient()
    payload = {'username': 'newuser2', 'email': 'a@a.com', 'password': '123'}

    response = client.post('/api/auth/register/', payload, format='json')

    assert response.status_code == 400


def test_me_requires_authentication():
    client = APIClient()
    response = client.get('/api/auth/me/')
    assert response.status_code == 401


def test_me_returns_current_user():
    user = User.objects.create_user(username='alice', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/auth/me/')

    assert response.status_code == 200
    assert response.data['username'] == 'alice'


def test_me_exposes_effective_permissions_from_roles():
    user = User.objects.create_user(username='carol', password='pass1234')
    user.roles.add(Role.objects.get(name='user'))
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/auth/me/')

    assert response.status_code == 200
    assert response.data['roles'] == ['user']
    assert 'add_customer' in response.data['permissions']
    assert 'view_customer' in response.data['permissions']
    assert 'delete_customer' not in response.data['permissions']


def test_me_permissions_are_empty_without_roles():
    user = User.objects.create_user(username='dave', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/auth/me/')

    assert response.status_code == 200
    assert response.data['permissions'] == []


def test_user_role_can_create_and_read_customers_but_not_delete():
    user = User.objects.create_user(username='bob', password='pass1234')
    user.roles.add(Role.objects.get(name='user'))
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        '/api/customers/',
        {'name': 'Acme Corp', 'email': 'contact@acme.test'},
        format='json',
    )
    assert response.status_code == 201, response.data
    assert response.data['name'] == 'Acme Corp'

    customer_id = response.data['id']
    assert client.get('/api/customers/').status_code == 200
    assert client.delete(f'/api/customers/{customer_id}/').status_code == 403


def test_authenticated_user_without_role_is_forbidden_on_customers():
    user = User.objects.create_user(username='no_permission_user', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        '/api/customers/',
        {'name': 'Acme Corp', 'email': 'contact@acme.test'},
        format='json',
    )

    assert response.status_code == 403


def test_customers_require_authentication():
    client = APIClient()
    response = client.get('/api/customers/')
    assert response.status_code == 401


def test_only_admin_can_manage_roles():
    user = User.objects.create_user(username='regular', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post('/api/roles/', {'name': 'manager'}, format='json')

    assert response.status_code == 403


def test_admin_can_create_role_and_assign_it_to_user():
    admin = make_admin(User.objects.create_user(username='admin', password='pass1234'))
    target_user = User.objects.create_user(username='employee', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=admin)

    role_response = client.post('/api/roles/', {'name': 'manager'}, format='json')
    assert role_response.status_code == 201

    assign_response = client.post(
        f'/api/users/{target_user.id}/assign_role/', {'role': 'manager'}, format='json'
    )
    assert assign_response.status_code == 200
    assert 'manager' in assign_response.data['roles']

    remove_response = client.post(
        f'/api/users/{target_user.id}/remove_role/', {'role': 'manager'}, format='json'
    )
    assert remove_response.status_code == 200
    assert 'manager' not in remove_response.data['roles']


def test_assign_unknown_role_returns_404():
    admin = make_admin(User.objects.create_user(username='admin2', password='pass1234'))
    target_user = User.objects.create_user(username='employee2', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.post(
        f'/api/users/{target_user.id}/assign_role/', {'role': 'inconnu'}, format='json'
    )

    assert response.status_code == 404


def test_users_list_requires_admin():
    user = User.objects.create_user(username='regular2', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/users/')

    assert response.status_code == 403


def test_admin_role_grants_access_without_is_staff():
    user = make_admin(User.objects.create_user(username='role_only_admin', password='pass1234'))
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/roles/')

    assert response.status_code == 200
    assert user.is_staff is False


def test_regular_user_without_admin_role_is_forbidden():
    user = User.objects.create_user(username='no_role_user', password='pass1234')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/roles/')

    assert response.status_code == 403
