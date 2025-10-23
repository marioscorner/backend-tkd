from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Conversation(models.Model):
    name = models.CharField(max_length=200, blank=True)  # para grupos
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Para evitar duplicados 1:1, guardaremos un “hash” opcional
    # cuando la conversación sea 1:1 (ordenado por id de usuario)
    one_to_one_key = models.CharField(max_length=255, blank=True, db_index=True)

    def __str__(self):
        return self.name or f"Conv {self.pk}"

class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_participations")
    joined_at = models.DateTimeField(auto_now_add=True)
    # Para contadores de no leídos
    last_read_at = models.DateTimeField(default=timezone.make_aware(timezone.datetime.min))

    class Meta:
        unique_together = ("conversation", "user")

    def __str__(self):
        return f"{self.user} in {self.conversation_id}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField(blank=True)
    # Si quieres adjuntos más tarde, crea un modelo de Attachment y relaciónalo aquí
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]  # latest first

    def __str__(self):
        return f"Msg {self.pk} by {self.sender_id}"

# Índices útiles (opcional, pero recomendado para escalar)
# from django.db.models import Index
# class Meta:
#     indexes = [
#         Index(fields=["conversation", "-created_at"]),
#         Index(fields=["sender", "-created_at"]),
#     ]
