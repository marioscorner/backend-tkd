# backend-tkd-main/chat/views.py
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from friends.utils import is_blocked_either

from .models import Conversation, ConversationParticipant, Message
from .serializers import (
    ConversationSerializer, ConversationCreateSerializer,
    MessageSerializer, MessageCreateSerializer
)
from .permissions import IsConversationParticipant
from .pagination import MessageCursorPagination

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
        serializer = self.get_serializer(conv, context={"request": request})
        return Response(serializer.data)

    @transaction.atomic
    @action(detail=False, methods=["post"], url_path="create")
    def create_conversation(self, request):
        serializer = ConversationCreateSerializer(data=request.data, context={"request": request})
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
            # ⛔ Check bloqueo
            other_id = next((u.id for u in users if u.id != current_user.id), None)
            if other_id and is_blocked_either(current_user.id, other_id):
                return Response(
                    {"detail": "No puedes iniciar chat: uno de los usuarios ha bloqueado al otro."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # 1:1: evitar duplicados
            uids = sorted([u.id for u in users])
            key = f"{uids[0]}:{uids[1]}"
            conv = Conversation.objects.filter(one_to_one_key=key).first()
            if conv:
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
        now = timezone.now()
        ConversationParticipant.objects.filter(conversation=conv, user=request.user)\
            .update(last_read_at=now)

        # 🔔 Emitir evento WS de read-receipt a la sala de la conversación
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"conv_{conv.id}",
            {
                "type": "chat.message",
                "event": "conversation.read",
                "by": request.user.id,
                "at": now.isoformat(),
            }
        )
        return Response({"status": "ok", "last_read_at": now.isoformat()})

class MessageViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    permission_classes = [IsAuthenticated, IsConversationParticipant]
    pagination_class = MessageCursorPagination

    def get_queryset(self):
        conv_id = self.kwargs.get("conversation_pk")
        if conv := Conversation.objects.filter(
            id=conv_id, participants__user=self.request.user
        ).first():
            return (Message.objects
                    .filter(conversation_id=conv_id, is_deleted=False)
                    .select_related("sender", "conversation")
                    .order_by("-created_at", "-id"))
        else:
            return Message.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return MessageCreateSerializer
        return MessageSerializer

    def list(self, request, *args, **kwargs):
        """
        Paginación por cursor: usa ?cursor=<token> y ?page_size=30.
        Orden: -created_at, -id.
        """
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        conv_id = self.kwargs.get("conversation_pk")
        # Verifica que el usuario sea participante
        conv = Conversation.objects.get(pk=conv_id)
        if not conv.participants.filter(user=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No perteneces a esta conversación.")

        # ⛔ Check de bloqueo en 1:1 antes de crear el mensaje
        if not conv.is_group:
            other_id = (ConversationParticipant.objects
                        .filter(conversation=conv)
                        .exclude(user_id=self.request.user.id)
                        .values_list("user_id", flat=True)
                        .first())
            if other_id and is_blocked_either(self.request.user.id, other_id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No puedes enviar mensajes: uno de los usuarios ha bloqueado al otro.")

        serializer.save(conversation=conv, sender=self.request.user)
