# backend-tkd-main/users/views.py
import contextlib
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator

from .serializers import (
    RegisterSerializer, UserSerializer, LoginSerializer,
    EmailVerificationRequestSerializer, EmailVerificationConfirmSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    LogoutSerializer,
)
from .tokens import email_verification_token
from .emails import send_verification_email, send_password_reset_email

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth-register"
    throttle_classes = [ScopedRateThrottle]

class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth-login"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.validated_data
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        # Claims útiles para el frontend
        access["role"] = user.role
        access["username"] = user.username
        access["email_verified"] = user.email_verified
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(access),
        })

class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

# --- Email verification ---
class EmailVerificationRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth-verify"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        s = EmailVerificationRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=s.validated_data["email"])
        except User.DoesNotExist:
            # 200 genérico para no filtrar existencia de correos
            return Response({"detail": "Si el email existe, se ha enviado un mensaje"})
        token = email_verification_token.make_token(user)
        send_verification_email(user, token)
        return Response({"detail": "Correo de verificación enviado"})

class EmailVerificationConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = EmailVerificationConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "Email verificado"})

# --- Password reset ---
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth-reset"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        s = PasswordResetRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=s.validated_data["email"])
        except User.DoesNotExist:
            return Response({"detail": "Si el email existe, se ha enviado un mensaje"})
        token = default_token_generator.make_token(user)
        send_password_reset_email(user, token)
        return Response({"detail": "Correo de reset enviado"})

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "Contraseña cambiada"})

# --- Logout con blacklist ---
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "auth-logout"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        s = LogoutSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        with contextlib.suppress(Exception):
            token = RefreshToken(s.validated_data["refresh"])
            token.blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)
