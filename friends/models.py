from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class FriendRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        CANCELED = "CANCELED", "Canceled"

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friend_requests_sent")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friend_requests_received")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    decided_at = models.DateTimeField(null=True, blank=True)
    message = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            # Evita duplicados directos
            UniqueConstraint(fields=["from_user", "to_user"], condition=Q(status="PENDING"), name="uniq_pending_request"),
        ]
        indexes = [
            models.Index(fields=["to_user", "status", "-created_at"]),
            models.Index(fields=["from_user", "status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} [{self.status}]"


class Friendship(models.Model):
    """
    Registro único por par (user1 < user2) para amistad recíproca.
    """
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friendships_as_user1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friendships_as_user2")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["user1", "user2"], name="uniq_friend_pair"),
            # Garantiza orden (user1_id < user2_id) a nivel lógico
        ]
        indexes = [
            models.Index(fields=["user1"]),
            models.Index(fields=["user2"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.user1} ⇄ {self.user2}"

    @staticmethod
    def normalize_pair(a_id: int, b_id: int):
        return (a_id, b_id) if a_id < b_id else (b_id, a_id)


class Block(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocks_initiated")
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocks_received")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["blocker", "blocked"], name="uniq_block")
        ]
        indexes = [
            models.Index(fields=["blocker"]),
            models.Index(fields=["blocked"]),
        ]

    def __str__(self):
        return f"{self.blocker} ⛔ {self.blocked}"
