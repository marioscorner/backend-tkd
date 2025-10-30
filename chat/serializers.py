# backend-tkd-main/chat/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Conversation, ConversationParticipant, Message
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

User = get_user_model()

# ---- Conversation ----
class ConversationParticipantMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationParticipant
        fields = ["user_id", "last_read_at"]

class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.IntegerField()))
    def get_participants(self, obj):
        # return list of user IDs, for example
        return list(obj.participants.values_list("id", flat=True))

class ConversationCreateSerializer(serializers.Serializer):
    is_group = serializers.BooleanField()
    name = serializers.CharField(required=False, allow_blank=True)
    users = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)

# ---- Message ----
class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]

class MessageSerializer(serializers.ModelSerializer):
    seen_by = serializers.SerializerMethodField()
    seen_by_other = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.IntegerField()))
    def get_seen_by(self, obj):
        return list(obj.seen_by.values_list("id", flat=True))

    @extend_schema_field(serializers.BooleanField())
    def get_seen_by_other(self, obj):
        # o el tipo que devuelva realmente
        return bool(...)  # lógica para determinar si lo ha visto el otro usuario

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["content"]  # conversation y sender vienen por la view
