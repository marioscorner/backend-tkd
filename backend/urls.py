from django.http import JsonResponse
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

def home(request):
    return JsonResponse({"message": "API Taekwondo Backend funcionando ✅"})

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/chat/', include('chat.urls')),
    path('api/docs/', include('docs.urls')),
]

