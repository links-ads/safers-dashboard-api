from .views_organizations import OrganizationView
from .views_roles import RoleView
from .views_auth import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    VerifyEmailView,
    ResendEmailVerificationView,
)
from .views_oauth2 import (
    LoginView as Oath2LoginView,
    LogoutView as Oauth2LogoutView,
    LogoutAllView as Oauth2LogoutAllView,
)
from .views_users import UserView
