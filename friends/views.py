from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import ScopedRateThrottle

from django.contrib.auth import get_user_model
from .models import FriendRequest
from .serializers import FriendRequestCreateSerializer
from . import services

User = get_user_model()


class FriendRequestCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "friends"

    def post(self, request, *args, **kwargs):
        ser = FriendRequestCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        target = ser.validated_data["target_user"]

        fr = services.create_friend_request(request.user, target)
        created = fr.status == "pending" and fr.from_user_id == request.user.id and fr.to_user_id == target.id

        return Response(
            {
                "id": fr.id,
                "from": fr.from_user_id,
                "to": fr.to_user_id,
                "status": fr.status,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class FriendRequestAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "friends"

    def post(self, request, id: int, *args, **kwargs):
        fr = get_object_or_404(FriendRequest, id=id)
        if fr.to_user_id != request.user.id:
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        friendship = services.accept_request(fr)
        return Response(
            {"friendship_id": friendship.id, "user1": friendship.user1_id, "user2": friendship.user2_id},
            status=status.HTTP_200_OK,
        )


class FriendRequestRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "friends"

    def post(self, request, id: int, *args, **kwargs):
        fr = get_object_or_404(FriendRequest, id=id)
        if fr.to_user_id != request.user.id:
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        services.reject_request(fr)
        return Response(status=status.HTTP_204_NO_CONTENT)
