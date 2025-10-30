# backend-tkd-main/friends/services.py
from django.utils import timezone
from django.db import transaction
from .models import FriendRequest, Friendship, Block

@transaction.atomic
def accept_request(fr: FriendRequest) -> Friendship:
    if fr.status != FriendRequest.Status.PENDING:
        raise ValueError("La solicitud no está pendiente.")
    fr.status = FriendRequest.Status.ACCEPTED
    fr.decided_at = timezone.now()
    fr.save(update_fields=["status", "decided_at"])
    a, b = Friendship.normalize_pair(fr.from_user_id, fr.to_user_id)
    friendship, _ = Friendship.objects.get_or_create(user1_id=a, user2_id=b)
    # Al aceptar, elimina otras solicitudes pendientes entre ambos (si las hubiese)
    FriendRequest.objects.filter(
        status=FriendRequest.Status.PENDING,
        from_user_id=fr.to_user_id, to_user_id=fr.from_user_id
    ).update(status=FriendRequest.Status.CANCELED, decided_at=timezone.now())
    return friendship

@transaction.atomic
def reject_request(fr: FriendRequest):
    if fr.status != FriendRequest.Status.PENDING:
        raise ValueError("La solicitud no está pendiente.")
    fr.status = FriendRequest.Status.REJECTED
    fr.decided_at = timezone.now()
    fr.save(update_fields=["status", "decided_at"])

@transaction.atomic
def cancel_request(fr: FriendRequest):
    if fr.status != FriendRequest.Status.PENDING:
        raise ValueError("La solicitud no está pendiente.")
    fr.status = FriendRequest.Status.CANCELED
    fr.decided_at = timezone.now()
    fr.save(update_fields=["status", "decided_at"])

def are_friends(user_id: int, other_id: int) -> bool:
    a, b = Friendship.normalize_pair(user_id, other_id)
    from .models import Friendship as F
    return F.objects.filter(user1_id=a, user2_id=b).exists()

def is_blocked(user_id: int, other_id: int) -> bool:
    from .models import Block
    return Block.objects.filter(blocker_id=user_id, blocked_id=other_id).exists() or \
           Block.objects.filter(blocker_id=other_id, blocked_id=user_id).exists()
