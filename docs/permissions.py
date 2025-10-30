from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrInstructorOrReadOnly(BasePermission):
    """
    - Lectura (GET, HEAD, OPTIONS): cualquiera puede acceder (público)
    - Escritura (POST, PUT, PATCH, DELETE): solo ADMIN o INSTRUCTOR
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, "role", None) in ["ADMIN", "INSTRUCTOR"]
        )


class IsAdminInstructorAlumnoReadOnly(BasePermission):
    """
    - Lectura: usuarios autenticados (ADMIN, INSTRUCTOR, ALUMNO)
    - Escritura: solo ADMIN o INSTRUCTOR
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            user = request.user
            return bool(user and user.is_authenticated)
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, "role", None) in ["ADMIN", "INSTRUCTOR"]
        )
