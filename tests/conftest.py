import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def create_user(db):
    def _make_user(username, email, password="pass12345", role="ALUMNO", **extra):
        u = User.objects.create_user(username=username, email=email, password=password, **extra)
        u.role = role
        u.save(update_fields=["role"])
        return u
    return _make_user

@pytest.fixture
def admin_user(create_user):
    return create_user("admin1", "admin1@example.com", role="ADMIN")

@pytest.fixture
def instructor_user(create_user):
    return create_user("instr1", "instr1@example.com", role="INSTRUCTOR")

@pytest.fixture
def alumno_user(create_user):
    return create_user("alum1", "alum1@example.com", role="ALUMNO")

@pytest.fixture
def auth_client_factory():
    """
    Devuelve una fábrica que crea un APIClient autenticado con Bearer access token
    y también devuelve el refresh token por si lo necesitas en tests (logout).
    """
    def _make(user):
        client = APIClient()
        access = AccessToken.for_user(user)
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(access)}")
        return client, str(refresh)
    return _make
