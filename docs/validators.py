from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}

DEFAULT_MAX_SIZE = 20 * 1024 * 1024  # 20 MB

def validate_uploaded_file(file_obj):
    """
    Valida content-type y tamaño de archivo.
    """
    content_type = getattr(file_obj, "content_type", None)
    if not content_type or content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError("Tipo de archivo no permitido. Usa PDF o imagen (PNG/JPEG/WEBP).")

    max_size = getattr(settings, "DOCS_MAX_UPLOAD_SIZE", DEFAULT_MAX_SIZE)
    if file_obj.size > max_size:
        raise ValidationError(f"Archivo demasiado grande. Máximo {max_size // (1024*1024)} MB.")
