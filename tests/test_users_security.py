import pytest
from rest_framework_simplejwt.tokens import RefreshToken

def test_logout_blacklist_works(auth_client_factory, admin_user):
    client, refresh = auth_client_factory(admin_user)
    res = client.post("/api/users/logout/", {"refresh": refresh}, format="json")
    assert res.status_code in (205, 200)

def test_email_verify_request_existing_user(client, alumno_user):
    res = client.post("/api/users/email/verify/request/", {"email": alumno_user.email}, format="json")
    # En tu serializer devolvemos 200 si existe; 400 si no existe.
    assert res.status_code == 200

@pytest.mark.django_db
def test_email_verify_request_non_existing_user_returns_400(client):
    res = client.post("/api/users/email/verify/request/", {"email": "no@existe.com"}, format="json")
    assert res.status_code in (400,)

def test_password_reset_request_hides_existence(client, alumno_user):
    # Para usuario existente
    r1 = client.post("/api/users/password/reset/request/", {"email": alumno_user.email}, format="json")
    assert r1.status_code == 200
    # Para usuario NO existente (también 200)
    r2 = client.post("/api/users/password/reset/request/", {"email": "nadie@existe.com"}, format="json")
    assert r2.status_code == 200
