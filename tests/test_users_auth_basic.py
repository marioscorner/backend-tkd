import pytest
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

def test_register_login_refresh_profile_logout_flow(client):
    # 1) Registro
    reg = client.post("/api/users/register/", {
        "username": "nuevo",
        "email": "nuevo@example.com",
        "password": "pass12345",
        "role": "ALUMNO"
    }, format="json")
    assert reg.status_code in (201, 200)
    # 2) Login
    login = client.post("/api/users/login/", {
        "email": "nuevo@example.com",
        "password": "pass12345"
    }, format="json")
    assert login.status_code == 200
    access = login.data["access"]
    refresh = login.data["refresh"]

    # 3) Profile (GET)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    me = client.get("/api/users/profile/")
    assert me.status_code == 200
    assert me.data["email"] == "nuevo@example.com"

    # 4) Profile (PUT)
    upd = client.put("/api/users/profile/", {"username": "nuevo_edit"}, format="json")
    assert upd.status_code in (200, 202)
    me2 = client.get("/api/users/profile/")
    assert me2.data["username"] == "nuevo_edit"

    # 5) Refresh
    refresh_res = client.post("/api/users/token/refresh/", {"refresh": refresh}, format="json")
    assert refresh_res.status_code == 200
    assert "access" in refresh_res.data

    # 6) Logout (blacklist)
    logout = client.post("/api/users/logout/", {"refresh": refresh}, format="json")
    assert logout.status_code in (205, 200)

def test_login_wrong_password(client, create_user):
    create_user("u1", "u1@example.com", password="correcta", role="ALUMNO")
    res = client.post("/api/users/login/", {
        "email": "u1@example.com",
        "password": "incorrecta"
    }, format="json")
    assert res.status_code in (401, 400)

def test_profile_requires_token(client):
    res = client.get("/api/users/profile/")
    assert res.status_code in (401, 403)
