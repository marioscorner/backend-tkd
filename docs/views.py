from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import BeltLevel, Technique, Document
from .serializers import BeltLevelSerializer, TechniqueSerializer, DocumentSerializer
from .permissions import IsAdminOrInstructorWrite

class BeltLevelViewSet(viewsets.ModelViewSet):
    queryset = BeltLevel.objects.all().prefetch_related("techniques")
    serializer_class = BeltLevelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly & IsAdminOrInstructorWrite]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Si no estás autenticado o eres alumno, sólo niveles públicos
        if not user.is_authenticated or getattr(user, "role", "alumno") == "alumno":
            qs = qs.filter(is_public=True)
        return qs

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def techniques(self, request, pk=None):
        level = self.get_object()
        ser = TechniqueSerializer(level.techniques.all(), many=True)
        return Response(ser.data)

class TechniqueViewSet(viewsets.ModelViewSet):
    queryset = Technique.objects.select_related("level")
    serializer_class = TechniqueSerializer
    permission_classes = [IsAuthenticatedOrReadOnly & IsAdminOrInstructorWrite]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated or getattr(user, "role", "alumno") == "alumno":
            qs = qs.filter(level__is_public=True)
        # filtros opcionales ?level=ID & ?q=texto
        level_id = self.request.query_params.get("level")
        if level_id:
            qs = qs.filter(level_id=level_id)
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        return qs

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly & IsAdminOrInstructorWrite]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # visibilidad por rol
        # admin ve todo; instructor no ve admin-only; alumno ve alumno/public; anónimo sólo public
        role = getattr(user, "role", None) if user.is_authenticated else None
        if role == "ADMIN":
            return qs
        if role == "INSTRUCTOR":
            return qs.exclude(visibility="admin")
        if role == "ALUMNO":
            return qs.filter(visibility__in=["alumno", "public"])
        # anónimo
        return qs.filter(visibility="public")
