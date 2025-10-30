# backend-tkd-main/chat/pagination.py
from rest_framework.pagination import CursorPagination

class MessageCursorPagination(CursorPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "-created_at"  # tie-break con -id en queryset
