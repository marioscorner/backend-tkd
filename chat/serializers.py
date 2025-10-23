from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, ConversationParticipant, Message
from django.utils import timezone

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "content", "created_at", "edited_at", "is_deleted"]
        read_only_fields = ["id", "sender", "created_at", "edited_at", "is_deleted", "conversation"]

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["content"]

class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    class Meta:
        model = ConversationParticipant
        fields = ["user", "joined_at", "last_read_at"]

class ConversationSerializer(serializers.ModelSerializer):
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "name", "is_group", "created_at", "participants", "last_message", "unread_count"]

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        if not msg:
            return None
        return {
            "id": msg.id,
            "content": msg.content,
            "sender": {"id": msg.sender_id, "username": msg.sender.username},
            "created_at": msg.created_at,
        }

    def get_unread_count(self, obj):
        user = self.context["request"].user
        part = obj.participants.filter(user=user).first()
        if not part:
            return 0
        # mensajes después del last_read_at
        return obj.messages.filter(created_at__gt=part.last_read_at, is_deleted=False).count()

class ConversationCreateSerializer(serializers.Serializer):
    """
    Crea conversación 1:1 o grupo.
    Para 1:1: is_group=False, users=[id_otro]
    Para grupo: is_group=True, name, users=[lista de ids]
    """
    is_group = serializers.BooleanField(default=False)
    name = serializers.CharField(required=False, allow_blank=True)
    users = serializers.ListField(child=serializers.IntegerField(), min_length=1)

    def validate(self, data):
        if data.get("is_group") and not data.get("name"):
            raise serializers.ValidationError("Los grupos requieren 'name'.")
        return data
