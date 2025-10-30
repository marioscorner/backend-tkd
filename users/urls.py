from django.urls import path
from .views_auth import (
    RegisterView,
    LoginView,
    RefreshView,
    ProfileView,
    LogoutView,
)
from .views_security import (
    EmailVerifyRequestView,
    EmailVerifyConfirmView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", RefreshView.as_view(), name="token_refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Seguridad de cuenta
    path("email/verify/request/", EmailVerifyRequestView.as_view(), name="email_verify_request"),
    path("email/verify/confirm/", EmailVerifyConfirmView.as_view(), name="email_verify_confirm"),
    path("password/reset/request/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
