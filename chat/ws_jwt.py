import jwt
from django.conf import settings
from urllib.parse import parse_qs
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class JWTAuthMiddleware:
    """Extrae ?token=<JWT> del querystring y adjunta scope['user']."""
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddlewareInstance(scope, self.inner)

class JWTAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = scope
        self.inner = inner

    async def __call__(self, receive, send):
        query = parse_qs(self.scope.get("query_string", b"").decode())
        token = (query.get("token") or [None])[0]
        self.scope["user"] = None
        if token:
            try:
                access = AccessToken(token)  # valida firma y expiración
                user_id = access.get("user_id")
                if user_id:
                    try:
                        user = await User.objects.aget(pk=user_id)
                        self.scope["user"] = user
                    except User.DoesNotExist:
                        self.scope["user"] = None
            except Exception:
                self.scope["user"] = None
        inner = self.inner(self.scope)
        return await inner(receive, send)
