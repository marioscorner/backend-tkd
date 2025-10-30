from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .serializers_auth import LogoutSerializer
from .serializers import ProfileUpdateSerializer

User = get_user_model()

# Registro
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

# Login (JWT)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

# Refresh
class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

# Perfil / me
class ProfileView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileUpdateSerializer  # para updates

    def get(self, request, *args, **kwargs):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        # PUT = actualización completa pero aquí solo permitimos username
        serializer = self.get_serializer(request.user, data=request.data)
        return self._extracted_from_patch_4(serializer, request)

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        return self._extracted_from_patch_4(serializer, request)

    # TODO Rename this here and in `put` and `patch`
    def _extracted_from_patch_4(self, serializer, request):
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

# Logout con blacklist
class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer  # 👈 importante

    @extend_schema(
        request=LogoutSerializer,
        responses={
            205: OpenApiResponse(description="Logout correcto"),
            400: OpenApiResponse(description="Token inválido o faltante"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh"]
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout correcto."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"detail": "Token inválido o ya caducado."}, status=status.HTTP_400_BAD_REQUEST)