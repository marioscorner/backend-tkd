from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Conversation, ConversationParticipant, Message
from .serializers import (
    ConversationSerializer, ConversationCreateSerializer,
    MessageSerializer, MessageCreateSerializer
)
from .permissions import IsConversationParticipant

User = get_user_model()

class ConversationViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Conversation.objects.all().prefetch_related("participants__user")
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        # Solo conversaciones donde participa el usuario
        return (Conversation.objects
                .filter(participants__user=self.request.user)
                .prefetch_related("participants__user")
                .order_by("-created_at"))

    def retrieve(self, request, *args, **kwargs):
        conv = self.get_object()
        self.check_object_permissions(request, conv)
        serializer = self.get_serializer(conv)
        return Response(serializer.data)

    @transaction.atomic
    @action(detail=False, methods=["post"], url_path="create")
    def create_conversation(self, request):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_group = serializer.validated_data["is_group"]
        name = serializer.validated_data.get("name", "")
        users_ids = serializer.validated_data["users"]
        current_user = request.user

        # Asegurar que el usuario actual está incluido
        if current_user.id not in users_ids:
            users_ids.append(current_user.id)

        users = list(User.objects.filter(id__in=users_ids).distinct())
        if len(users) < 2:
            return Response({"detail": "Se requieren al menos 2 usuarios."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not is_group and len(users) != 2:
            return Response({"detail": "En 1:1 deben ser exactamente 2 usuarios."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not is_group:
            # 1:1: evitar duplicados
            uids = sorted([u.id for u in users])
            key = f"{uids[0]}:{uids[1]}"
            conv = Conversation.objects.filter(one_to_one_key=key).first()
            if conv:
                # Ya existe, devolverla
                data = ConversationSerializer(conv, context={"request": request}).data
                return Response(data, status=status.HTTP_200_OK)
            conv = Conversation.objects.create(is_group=False, one_to_one_key=key)
        else:
            conv = Conversation.objects.create(is_group=True, name=name)

        # Crear participantes
        parts = [ConversationParticipant(conversation=conv, user=u) for u in users]
        ConversationParticipant.objects.bulk_create(parts)

        data = ConversationSerializer(conv, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        conv = self.get_object()
        # Verifica pertenencia
        if not conv.participants.filter(user=request.user).exists():
            return Response(status=status.HTTP_403_FORBIDDEN)
        # Actualiza last_read_at
        ConversationParticipant.objects.filter(conversation=conv, user=request.user)\
            .update(last_read_at=timezone.now())
        return Response({"status": "ok"})

class MessageViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    permission_classes = [IsAuthenticated, IsConversationParticipant]

    def get_queryset(self):
        conv_id = self.kwargs.get("conversation_pk")
        # Validación básica: el usuario debe ser participante
        conv = Conversation.objects.filter(id=conv_id, participants__user=self.request.user).first()
        if not conv:
            return Message.objects.none()
        return Message.objects.filter(conversation_id=conv_id, is_deleted=False).select_related("sender")

    def get_serializer_class(self):
        if self.action == "create":
            return MessageCreateSerializer
        return MessageSerializer

    def list(self, request, *args, **kwargs):
        """
        Paginación por query param ?cursor=<iso-datetime|id>, o usa paginación estándar DRF.
        Para simpleza, usamos paginación estándar si la tienes configurada.
        """
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        conv_id = self.kwargs.get("conversation_pk")
        # Verifica que el usuario sea participante
        conv = Conversation.objects.get(pk=conv_id)
        if not conv.participants.filter(user=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No perteneces a esta conversación.")
        serializer.save(conversation=conv, sender=self.request.user)
