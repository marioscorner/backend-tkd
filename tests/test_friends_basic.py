import pytest

pytestmark = pytest.mark.django_db

def test_friend_request_send_accept_and_appears_in_lists(auth_client_factory, create_user):
    # users
    a = create_user("alice", "alice@example.com", role="ALUMNO")
    b = create_user("bob", "bob@example.com", role="ALUMNO")

    ca, _ = auth_client_factory(a)
    cb, _ = auth_client_factory(b)

    # A envía solicitud a B
    r_send = ca.post("/api/friends/requests/", {"to": b.id}, format="json")
    assert r_send.status_code in (201, 200)
    req_id = r_send.data.get("id") or r_send.data.get("request_id")

    # B acepta
    r_accept = cb.post(f"/api/friends/requests/{req_id}/accept/", {}, format="json")
    assert r_accept.status_code in (200, 204)

    # Listas de amigos
    list_a = ca.get("/api/friends/")
    list_b = cb.get("/api/friends/")
    assert list_a.status_code == 200 and list_b.status_code == 200
    names_a = [item.get("username") or item.get("friend", {}).get("username") for item in (list_a.data.get("results") or list_a.data)]
    names_b = [item.get("username") or item.get("friend", {}).get("username") for item in (list_b.data.get("results") or list_b.data)]
    assert "bob" in names_a and "alice" in names_b

def test_friend_request_reject_flow(auth_client_factory, create_user):
    a = create_user("carlos", "carlos@example.com", role="ALUMNO")
    b = create_user("diana", "diana@example.com", role="ALUMNO")

    ca, _ = auth_client_factory(a)
    cb, _ = auth_client_factory(b)

    r_send = ca.post("/api/friends/requests/", {"to": b.id}, format="json")
    assert r_send.status_code in (201, 200)
    req_id = r_send.data.get("id") or r_send.data.get("request_id")

    r_reject = cb.post(f"/api/friends/requests/{req_id}/reject/", {}, format="json")
    assert r_reject.status_code in (200, 204)

    # No debería aparecer amistad
    list_a = ca.get("/api/friends/")
    list_b = cb.get("/api/friends/")
    names_a = [item.get("username") or item.get("friend", {}).get("username") for item in (list_a.data.get("results") or list_a.data)]
    names_b = [item.get("username") or item.get("friend", {}).get("username") for item in (list_b.data.get("results") or list_b.data)]
    assert "diana" not in names_a and "carlos" not in names_b

def test_friend_request_cancel_by_sender(auth_client_factory, create_user):
    a = create_user("eva", "eva@example.com", role="ALUMNO")
    b = create_user("felix", "felix@example.com", role="ALUMNO")

    ca, _ = auth_client_factory(a)

    r_send = ca.post("/api/friends/requests/", {"to": b.id}, format="json")
    assert r_send.status_code in (201, 200)
    req_id = r_send.data.get("id") or r_send.data.get("request_id")

    r_cancel = ca.post(f"/api/friends/requests/{req_id}/cancel/", {}, format="json")
    assert r_cancel.status_code in (200, 204)

def test_block_and_unfriend(auth_client_factory, create_user):
    admin = create_user("adminx", "adminx@example.com", role="ADMIN")
    x = create_user("gabi", "gabi@example.com", role="ALUMNO")
    y = create_user("hector", "hector@example.com", role="ALUMNO")

    c_admin, _ = auth_client_factory(admin)
    cx, _ = auth_client_factory(x)
    cy, _ = auth_client_factory(y)

    # x <-> y se hacen amigos
    r1 = cx.post("/api/friends/requests/", {"to": y.id}, format="json")
    assert r1.status_code in (201, 200)
    req_id = r1.data.get("id") or r1.data.get("request_id")
    r2 = cy.post(f"/api/friends/requests/{req_id}/accept/", {}, format="json")
    assert r2.status_code in (200, 204)

    # Unfriend (endpoint típico como POST /api/friends/unfriend/{user_id}/)
    un = cx.post(f"/api/friends/unfriend/{y.id}/", {}, format="json")
    assert un.status_code in (200, 204)

    # Bloqueo (POST /api/friends/block/{user_id}/ y DELETE /api/friends/block/{user_id}/)
    b1 = cx.post(f"/api/friends/block/{y.id}/", {}, format="json")
    assert b1.status_code in (201, 200, 204)
    b2 = cx.delete(f"/api/friends/block/{y.id}/")
    assert b2.status_code in (204, 200)
