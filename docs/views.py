from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser

from users.permissions import IsEmailVerified
from .models import BeltLevel as Level, Technique, Document
from .serializers import LevelSerializer, TechniqueSerializer, DocumentSerializer
from .permissions import (
    IsAdminOrInstructorOrReadOnly,
    IsAdminInstructorAlumnoReadOnly,
)

# ------------------------------
# 🔹 Paginación por defecto
# ------------------------------
class DefaultPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ------------------------------
# 🔹 Niveles (lectura pública)
# ------------------------------
class LevelListCreateView(generics.ListCreateAPIView):
    queryset = Level.objects.all().order_by("order", "id")
    serializer_class = LevelSerializer
    permission_classes = [IsAdminOrInstructorOrReadOnly]
    pagination_class = DefaultPagination


class LevelDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsAdminOrInstructorOrReadOnly]


# ------------------------------
# 🔹 Técnicas (lectura pública)
# ------------------------------
class TechniqueListCreateView(generics.ListCreateAPIView):
    serializer_class = TechniqueSerializer
    permission_classes = [IsAdminOrInstructorOrReadOnly]
    pagination_class = DefaultPagination

    def get_queryset(self):
        queryset = Technique.objects.select_related("level").all()
        level_id = self.request.query_params.get("level")
        q = self.request.query_params.get("q")

        if level_id:
            queryset = queryset.filter(level_id=level_id)
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        return queryset.order_by("id")


class TechniqueDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Technique.objects.select_related("level").all()
    serializer_class = TechniqueSerializer
    permission_classes = [IsAdminOrInstructorOrReadOnly]


# ------------------------------
# 🔹 Documentos (solo autenticados)
# ------------------------------

class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAdminInstructorAlumnoReadOnly]
    pagination_class = DefaultPagination
    parser_classes = [MultiPartParser, FormParser]  # 👈 IMPORTANTE

    def get_queryset(self):
        user = self.request.user
        qs = Document.objects.all().order_by("-created_at", "id")
        if not user.is_authenticated:
            return qs.filter(visibility="public")
        role = getattr(user, "role", "ALUMNO")
        if role == "ADMIN":
            return qs
        if role == "INSTRUCTOR":
            return qs.filter(visibility__in=["public", "instructor", "alumno"])
        if role == "ALUMNO":
            return qs.filter(visibility__in=["public", "alumno"])
        return qs.filter(visibility="public")

class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAdminInstructorAlumnoReadOnly]
