from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

# Para anidar mensajes bajo conversaciones:
# /api/chat/conversations/<id>/messages/
messages_list = MessageViewSet.as_view({'get': 'list', 'post': 'create'})

urlpatterns = [
    path('', include(router.urls)),
    path('conversations/<int:conversation_pk>/messages/', messages_list, name='conversation-messages'),
]