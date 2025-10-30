# backend-tkd-main/chat/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Conversation, Message, ConversationParticipant
from friends.utils import is_blocked_either  # helper de bloqueo

User = get_user_model()

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"conv_{self.conversation_id}"

        # Debe estar autenticado y ser participante
        if not self.user or not await self._is_participant(self.conversation_id, self.user.id):
            await self.close()
            return

        # ⛔ Bloqueo en 1:1: si existe, se rechaza la conexión
        if await self._is_one_to_one(self.conversation_id):
            other_id = await self._get_other_participant_id(self.conversation_id, self.user.id)
            if other_id and await self._is_blocked(self.user.id, other_id):
                await self.close()
                return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = content.get("action")

        if action == "message":
            text = (content.get("content") or "").strip()
            if text:
                # ⛔ Check bloqueo 1:1
                if await self._is_one_to_one(self.conversation_id):
                    other_id = await self._get_other_participant_id(self.conversation_id, self.user.id)
                    if other_id and await self._is_blocked(self.user.id, other_id):
                        await self.send_json({"type": "error", "detail": "Bloqueo activo: no puedes enviar mensajes."})
                        return

                msg = await self._create_message(self.conversation_id, self.user.id, text)
                await self.channel_layer.group_send(self.group_name, {
                    "type": "chat.message",
                    "event": "message.new",
                    "message": {
                        "id": msg["id"],
                        "content": msg["content"],
                        "sender": {"id": msg["sender_id"], "username": msg["sender_username"]},
                        "created_at": msg["created_at"].isoformat(),
                    },
                })

        elif action == "read":
            await self._mark_read(self.conversation_id, self.user.id)
            await self.channel_layer.group_send(self.group_name, {
                "type": "chat.message",
                "event": "conversation.read",
                "by": self.user.id,
                "at": timezone.now().isoformat(),
            })

        elif action == "typing.start":
            await self.channel_layer.group_send(self.group_name, {
                "type": "chat.message",
                "event": "typing.start",
                "by": self.user.id,
                "at": timezone.now().isoformat(),
            })

        elif action == "typing.stop":
            await self.channel_layer.group_send(self.group_name, {
                "type": "chat.message",
                "event": "typing.stop",
                "by": self.user.id,
                "at": timezone.now().isoformat(),
            })

    async def chat_message(self, event):
        await self.send_json(event)

    # ----------------------
    # DB helpers (sync -> async)
    # ----------------------
    @database_sync_to_async
    def _is_participant(self, conv_id, user_id):
        return ConversationParticipant.objects.filter(conversation_id=conv_id, user_id=user_id).exists()

    @database_sync_to_async
    def _is_one_to_one(self, conv_id):
        try:
            return not Conversation.objects.values_list("is_group", flat=True).get(pk=conv_id)
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def _get_other_participant_id(self, conv_id, current_user_id):
        return (ConversationParticipant.objects
                .filter(conversation_id=conv_id)
                .exclude(user_id=current_user_id)
                .values_list("user_id", flat=True)
                .first())

    @database_sync_to_async
    def _is_blocked(self, a_id, b_id):
        return is_blocked_either(a_id, b_id)

    @database_sync_to_async
    def _create_message(self, conv_id, user_id, content):
        m = Message.objects.create(conversation_id=conv_id, sender_id=user_id, content=content)
        return {
            "id": m.id,
            "content": m.content,
            "sender_id": m.sender_id,
            "sender_username": m.sender.username,
            "created_at": m.created_at,
        }

    @database_sync_to_async
    def _mark_read(self, conv_id, user_id):
        ConversationParticipant.objects.filter(conversation_id=conv_id, user_id=user_id)\
            .update(last_read_at=timezone.now())