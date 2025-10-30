from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from .tokens import email_verification_token, password_reset_token

User = get_user_model()

# Cambia en prod
FRONTEND_URL = "http://localhost:3000"

class EmailVerifyRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("No existe un usuario con ese email.")
        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        url = f"{FRONTEND_URL}/verify-email?uid={uid}&token={token}"
        send_mail(
            "Verifica tu correo",
            f"Hola {user.username}, verifica tu cuenta aquí:\n{url}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        return {"sent": True}


class EmailVerifyConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=uid)
        except Exception:
            raise serializers.ValidationError("UID inválido.")

        if not email_verification_token.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Token inválido o caducado.")
        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        # Asumimos que tu modelo User tiene email_verified=True/False
        if hasattr(user, "email_verified"):
            user.email_verified = True
            user.save(update_fields=["email_verified"])
        return {"verified": True}


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            user = None
        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        if not user:
            # No reveles si existe o no
            return {"sent": True}
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        url = f"{FRONTEND_URL}/reset-password?uid={uid}&token={token}"
        send_mail(
            "Restablece tu contraseña",
            f"Hola {user.username}, restablece tu contraseña aquí:\n{url}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        return {"sent": True}


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=uid)
        except Exception:
            raise serializers.ValidationError("UID inválido.")

        if not password_reset_token.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Token inválido o caducado.")
        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return {"reset": True}
