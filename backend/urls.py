from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API apps
    path('api/users/', include('users.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/friends/', include('friends.urls')),
    path('api/docs/', include('docs.urls')),

    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
