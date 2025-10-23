from rest_framework.permissions import BasePermission

class IsConversationParticipant(BasePermission):
    """
    Permite acceso solo si el usuario forma parte de la conversación.
    """
    def has_object_permission(self, request, view, obj):
        # obj puede ser Conversation o Message
        if hasattr(obj, "participants"):  # Conversation
            return obj.participants.filter(user=request.user).exists()
        if hasattr(obj, "conversation"):   # Message
            return obj.conversation.participants.filter(user=request.user).exists()
        return False
