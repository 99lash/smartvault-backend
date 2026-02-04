from app.core.settings import settings
from app.infrastructure.notifications.email_service import DevEmailService, EmailService, SMTPEmailService
from app.infrastructure.services.otp_ticket_service import OTPTicketService

_email_service: EmailService | None = None
_otp_ticket_service = OTPTicketService()


def _build_email_service() -> EmailService:
    backend = settings.resolved_email_backend.lower()

    if backend == "smtp":
        if not settings.SMTP_HOST:
            raise ValueError("SMTP_HOST must be set when EMAIL_BACKEND=smtp")
        from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        if not from_email:
            raise ValueError("SMTP_FROM_EMAIL or SMTP_USER must be set for SMTP email backend")

        return SMTPEmailService(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT or 587,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            from_email=from_email,
            from_name=settings.SMTP_FROM_NAME,
            use_tls=True,
        )

    return DevEmailService()


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = _build_email_service()
    return _email_service


def get_otp_ticket_service() -> OTPTicketService:
    return _otp_ticket_service
