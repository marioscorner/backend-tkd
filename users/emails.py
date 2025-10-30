# backend-tkd-main/users/emails.py
from django.conf import settings
from django.core.mail import send_mail

def _origin():
    return getattr(settings, "FRONTEND_ORIGIN", "http://localhost:5173").rstrip("/")

def send_verification_email(user, token: str):
    url = f"{_origin()}/verify-email?uid={user.pk}&token={token}"
    subject = "Verifica tu correo"
    body = (
        "Hola,\n\n"
        "Para activar tu cuenta, confirma tu correo en el siguiente enlace:\n"
        f"{url}\n\n"
        "Si no has solicitado esto, ignora este mensaje."
    )
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])

def send_password_reset_email(user, token: str):
    url = f"{_origin()}/reset-password?uid={user.pk}&token={token}"
    subject = "Restablecer contraseña"
    body = (
        "Hola,\n\n"
        "Has solicitado restablecer tu contraseña. Usa el siguiente enlace:\n"
        f"{url}\n\n"
        "Si no has solicitado esto, ignora este mensaje."
    )
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
