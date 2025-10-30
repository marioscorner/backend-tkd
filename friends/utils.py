# backend-tkd-main/friends/utils.py
from .models import Block

def is_blocked_either(a_id: int, b_id: int) -> bool:
    return Block.objects.filter(blocker_id=a_id, blocked_id=b_id).exists() or \
           Block.objects.filter(blocker_id=b_id, blocked_id=a_id).exists()
