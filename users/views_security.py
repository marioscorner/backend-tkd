from rest_framework import generics, permissions
from rest_framework.response import Response
from .serializers_security import (
    EmailVerifyRequestSerializer,
    EmailVerifyConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

class EmailVerifyRequestView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerifyRequestSerializer

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.save()
        return Response(data)

class EmailVerifyConfirmView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerifyConfirmSerializer

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.save()
        return Response(data)

class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.save()
        return Response(data)

class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.save()
        return Response(data)
