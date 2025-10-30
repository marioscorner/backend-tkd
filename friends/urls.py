# backend/friends/urls.py
from django.urls import path
from .views import (
    FriendRequestCreateView,
    FriendRequestAcceptView,
    FriendRequestRejectView,
    FriendsListView,
)

urlpatterns = [
    path("requests/", FriendRequestCreateView.as_view(), name="friendrequest-create"),
    path("requests/<int:id>/accept/", FriendRequestAcceptView.as_view(), name="friendrequest-accept"),
    path("requests/<int:id>/reject/", FriendRequestRejectView.as_view(), name="friendrequest-reject"),
    path("", FriendsListView.as_view(), name="friends-list"),
]
