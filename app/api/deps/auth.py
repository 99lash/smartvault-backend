from app.infrastructure.notifications.email_service import DevEmailService, EmailService
from app.infrastructure.services.otp_ticket_service import OTPTicketService

_email_service: EmailService = DevEmailService()
_otp_ticket_service = OTPTicketService()


def get_email_service() -> EmailService:
    return _email_service


def get_otp_ticket_service() -> OTPTicketService:
    return _otp_ticket_service
