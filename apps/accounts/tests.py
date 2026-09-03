import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

User = get_user_model()


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
