import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from docs.models import BeltLevel as Level, Technique, Document

# -----------------------------
# Public access (niveles / técnicas)
# -----------------------------

def test_levels_public_list_ok(client, db):
    Level.objects.create(name="Blanco", order=1, is_public=True)
    res = client.get("/api/docs/levels/")
    assert res.status_code == 200
    assert len(res.data["results"]) == 1 or isinstance(res.data, list)  # por si no usas paginación en tu settings

def test_techniques_public_list_ok(client, db):
    lvl = Level.objects.create(name="Amarillo", order=2, is_public=True)
    Technique.objects.create(level=lvl, name="Ap Chagi", description="")
    res = client.get("/api/docs/techniques/")
    assert res.status_code == 200
    # resultados pueden venir paginados o en lista
    assert "results" in res.data or isinstance(res.data, list)

# -----------------------------
# Documentos (requieren autenticación)
# -----------------------------

def test_documents_unauth_requires_token(client, db):
    Document.objects.create(title="Normas", visibility="public", file=SimpleUploadedFile("a.pdf", b"x"))
    res = client.get("/api/docs/documents/")
    assert res.status_code in (401, 403)  # 401 si no hay token; 403 si tu permiso exige login en SAFE_METHODS

def test_documents_visibility_by_role(auth_client_factory, admin_user, instructor_user, alumno_user, db):
    # Crea documentos con distintas visibilidades
    def mkdoc(title, vis):
        return Document.objects.create(
            title=title,
            visibility=vis,
            file=SimpleUploadedFile(f"{title}.pdf", b"%PDF-1.4")
        )
    d_pub = mkdoc("Publico", "public")
    d_al  = mkdoc("Alumno", "alumno")
    d_ins = mkdoc("Instructor", "instructor")
    d_adm = mkdoc("Admin", "admin")

    # ALUMNO: ve public + alumno
    c_al, _ = auth_client_factory(alumno_user)
    r_al = c_al.get("/api/docs/documents/")
    assert r_al.status_code == 200
    titles_al = [x["title"] for x in (r_al.data.get("results") or r_al.data)]
    assert "Publico" in titles_al and "Alumno" in titles_al
    assert "Instructor" not in titles_al and "Admin" not in titles_al

    # INSTRUCTOR: ve public + alumno + instructor
    c_ins, _ = auth_client_factory(instructor_user)
    r_ins = c_ins.get("/api/docs/documents/")
    assert r_ins.status_code == 200
    titles_ins = [x["title"] for x in (r_ins.data.get("results") or r_ins.data)]
    assert "Publico" in titles_ins and "Alumno" in titles_ins and "Instructor" in titles_ins
    assert "Admin" not in titles_ins

    # ADMIN: ve todo
    c_adm, _ = auth_client_factory(admin_user)
    r_adm = c_adm.get("/api/docs/documents/")
    assert r_adm.status_code == 200
    titles_adm = [x["title"] for x in (r_adm.data.get("results") or r_adm.data)]
    assert {"Publico", "Alumno", "Instructor", "Admin"}.issubset(set(titles_adm))

# -----------------------------
# Permisos de escritura
# -----------------------------

def test_level_create_permissions(client, auth_client_factory, alumno_user, instructor_user, admin_user, db):
    payload = {"name": "Naranja", "order": 3, "is_public": True}

    # Anónimo: debe poder leer pero NO crear (405 si ruta no permite POST, o 401/403)
    res_anon = client.post("/api/docs/levels/", payload, format="json")
    assert res_anon.status_code in (401, 403)

    # ALUMNO autenticado: solo lectura
    c_al, _ = auth_client_factory(alumno_user)
    res_al = c_al.post("/api/docs/levels/", payload, format="json")
    assert res_al.status_code in (403,)  # ReadOnly para alumno

    # INSTRUCTOR: puede crear
    c_ins, _ = auth_client_factory(instructor_user)
    res_ins = c_ins.post("/api/docs/levels/", payload, format="json")
    assert res_ins.status_code in (201, 200)

    # ADMIN: puede crear
    c_adm, _ = auth_client_factory(admin_user)
    res_adm = c_adm.post("/api/docs/levels/", {"name": "Verde", "order": 4, "is_public": True}, format="json")
    assert res_adm.status_code in (201, 200)

def test_technique_create_permissions(client, auth_client_factory, alumno_user, instructor_user, admin_user, db):
    level = Level.objects.create(name="Azul", order=5, is_public=True)
    payload = {"level": level.id, "name": "Yop Chagi", "description": ""}

    # alumno no puede
    c_al, _ = auth_client_factory(alumno_user)
    r_al = c_al.post("/api/docs/techniques/", payload, format="json")
    assert r_al.status_code in (403,)

    # instructor sí
    c_ins, _ = auth_client_factory(instructor_user)
    r_ins = c_ins.post("/api/docs/techniques/", payload, format="json")
    assert r_ins.status_code in (201, 200)

    # admin sí
    c_adm, _ = auth_client_factory(admin_user)
    r_adm = c_adm.post("/api/docs/techniques/", {"level": level.id, "name": "Dollyo Chagi", "description": ""}, format="json")
    assert r_adm.status_code in (201, 200)

def test_document_create_permissions(auth_client_factory, alumno_user, instructor_user, admin_user, db):
    # alumno NO puede crear
    c_al, _ = auth_client_factory(alumno_user)
    file1 = SimpleUploadedFile("doc1.pdf", b"%PDF-1.4")
    r_al = c_al.post("/api/docs/documents/", {"title": "Doc1", "visibility": "alumno", "file": file1}, format="multipart")
    assert r_al.status_code in (403,)

    # instructor SÍ
    c_ins, _ = auth_client_factory(instructor_user)
    file2 = SimpleUploadedFile("doc2.pdf", b"%PDF-1.4")
    r_ins = c_ins.post("/api/docs/documents/", {"title": "Doc2", "visibility": "alumno", "file": file2}, format="multipart")
    assert r_ins.status_code in (201, 200)

    # admin SÍ
    c_adm, _ = auth_client_factory(admin_user)
    file3 = SimpleUploadedFile("doc3.pdf", b"%PDF-1.4")
    r_adm = c_adm.post("/api/docs/documents/", {"title": "Doc3", "visibility": "admin", "file": file3}, format="multipart")
    assert r_adm.status_code in (201, 200)
