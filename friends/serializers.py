from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import FriendRequest, Friendship, Block

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        ref_name = "FriendUserMiniSerializer"  # Evita conflictos en la documentación

class FriendRequestCreateSerializer(serializers.Serializer):
    # aceptamos ambos por compatibilidad
    to = serializers.IntegerField(required=False)
    to_user = serializers.IntegerField(required=False)

    def validate(self, attrs):
        request = self.context.get("request")
        to_id = attrs.get("to") or attrs.get("to_user")
        if not to_id:
            raise serializers.ValidationError({"to": "Este campo es requerido."})
        try:
            target = User.objects.get(id=to_id)
        except User.DoesNotExist as e:
            raise serializers.ValidationError({"to": "Usuario destino no existe."}) from e
        if request and request.user.id == target.id:
            raise serializers.ValidationError("No puedes enviarte una solicitud a ti mismo.")
        # normalizamos:
        attrs["target_user"] = target
        return attrs

class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserMiniSerializer(read_only=True)
    to_user = UserMiniSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ["id", "from_user", "to_user", "status", "message", "created_at", "decided_at"]

class FriendshipSerializer(serializers.ModelSerializer):
    friend = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ["id", "friend", "created_at"]

    def get_friend(self, obj):
        u = self.context["request"].user
        other = obj.user2 if obj.user1_id == u.id else obj.user1
        return UserMiniSerializer(other).data

class FriendListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
class BlockSerializer(serializers.ModelSerializer):
    blocked = UserMiniSerializer(read_only=True)

    class Meta:
        model = Block
        fields = ["id", "blocked", "created_at"]
        