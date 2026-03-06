from app.core.settings import settings
from redis import Redis
from app.application.ports.email_service import EmailService
from app.application.services.email_notification_service import EmailNotificationService
from app.infrastructure.notifications.email_service import DevEmailService, EmailJSEmailService, ResendEmailService, SMTPEmailService
from app.infrastructure.services.otp_ticket_service import OTPTicketService
from app.infrastructure.services.password_reset_service import PasswordResetService
from app.infrastructure.security.rate_limiter import RateLimiter
from app.application.services.token_service import TokenService
from app.application.use_cases.reset_password import RequestPasswordReset, ConfirmPasswordReset
from app.infrastructure.services.refresh_token_store import RedisRefreshTokenStore
from app.api.deps.users import get_user_repo, get_password_hasher
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

_email_service: EmailService | None = None
_otp_ticket_service = OTPTicketService()
_password_reset_service = PasswordResetService()
_rate_limiter = RateLimiter()
oauth2_scheme = HTTPBearer()

def get_redis_client() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=False)

def get_refresh_token_store() -> RedisRefreshTokenStore:
    redis = get_redis_client()
    return RedisRefreshTokenStore(redis)

def _build_email_service() -> EmailService:
    """Build email service with metrics tracking."""
    backend = settings.resolved_email_backend.lower()
    if backend == "smtp":
        if not settings.SMTP_HOST:
            raise ValueError("SMTP_HOST must be set when EMAIL_BACKEND=smtp")
        from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        if not from_email:
            raise ValueError("SMTP_FROM_EMAIL or SMTP_USER must be set for SMTP email backend")

        base_service = SMTPEmailService(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT or 587,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            from_email=from_email,
            from_name=settings.SMTP_FROM_NAME,
            use_tls=True,
        )
    elif backend == "emailjs":
        missing = [
            k for k, v in {
                "EMAILJS_SERVICE_ID": settings.EMAILJS_SERVICE_ID,
                "EMAILJS_TEMPLATE_ID": settings.EMAILJS_TEMPLATE_ID,
                "EMAILJS_PUBLIC_KEY": settings.EMAILJS_PUBLIC_KEY,
                "EMAILJS_PRIVATE_KEY": settings.EMAILJS_PRIVATE_KEY,
            }.items() if not v
        ]
        if missing:
            raise ValueError(f"Missing EmailJS config: {', '.join(missing)}")
        base_service = EmailJSEmailService(
            service_id=settings.EMAILJS_SERVICE_ID,
            template_id=settings.EMAILJS_TEMPLATE_ID,
            public_key=settings.EMAILJS_PUBLIC_KEY,
            private_key=settings.EMAILJS_PRIVATE_KEY,
            otp_ttl_seconds=settings.OTP_TTL_SECONDS,
        )
    elif backend == "resend":
        if not settings.RESEND_API_KEY:
            raise ValueError("RESEND_API_KEY must be set when EMAIL_BACKEND=resend")
        base_service = ResendEmailService(
            api_key=settings.RESEND_API_KEY,
            from_email=settings.RESEND_FROM_EMAIL,
            from_name=settings.RESEND_FROM_NAME,
            otp_ttl_seconds=settings.OTP_TTL_SECONDS,
        )
    else:
        base_service = DevEmailService()
    
    # Wrap with metrics tracking
    from app.infrastructure.notifications.email_metrics import (
        increment_email_sent,
        increment_email_failed,
    )

    return EmailNotificationService(
        email_service=base_service,
        on_sent=increment_email_sent,
        on_failed=increment_email_failed,
    )

def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = _build_email_service()
    return _email_service

def get_otp_ticket_service() -> OTPTicketService:
    return _otp_ticket_service

def get_password_reset_service() -> PasswordResetService:
    return _password_reset_service

def get_rate_limiter() -> RateLimiter:
    return _rate_limiter

def get_token_service() -> TokenService:
    store = get_refresh_token_store()
    return TokenService(store)

def get_request_password_reset_uc(
    repo=Depends(get_user_repo),
    reset_svc=Depends(get_password_reset_service),
    email_svc=Depends(get_email_service),
) -> RequestPasswordReset:
    return RequestPasswordReset(repo, reset_svc, email_svc)

def get_confirm_password_reset_uc(
    repo=Depends(get_user_repo),
    reset_svc=Depends(get_password_reset_service),
    hasher=Depends(get_password_hasher),
) -> ConfirmPasswordReset:
    return ConfirmPasswordReset(repo, reset_svc, hasher)

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> str:
    token = credentials.credentials
    # 1. Test Bypass (Critical for acceptance criteria)
    if settings.DEV_AUTH_BYPASS:
        return "test-user-id"

    # 2. JWT Verification
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception