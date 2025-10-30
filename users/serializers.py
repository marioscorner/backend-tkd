from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "email_verified"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):

    username_field = "email"

    def validate(self, attrs):
        data = super().validate(attrs)  # genera access/refresh y setea self.user
        data["user"] = UserSerializer(self.user).data  # <- importante: no devolver objeto crudo
        return data

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # permite editar lo que necesitas; aquí solo username
        fields = ["username"]