"""
Email service implementations.

Provides concrete adapters for different email backends (SMTP, Dev, EmailJS, Resend).

Clean Architecture:
    Infrastructure layer — implements EmailService port from application layer.
"""
from __future__ import annotations

import logging
from email.message import EmailMessage
from email.utils import formataddr

import httpx

try:
    import aiosmtplib  # type: ignore
except ImportError:  # pragma: no cover - only hit when optional dep missing
    aiosmtplib = None  # type: ignore

log = logging.getLogger(__name__)

_EMAILJS_API_URL = "https://api.emailjs.com/api/v1.0/email/send"
_RESEND_API_URL = "https://api.resend.com/emails"


class ResendEmailService:
    def __init__(
        self,
        *,
        api_key: str,
        from_email: str = "onboarding@resend.dev",
        from_name: str | None = "SmartVault",
        otp_ttl_seconds: int = 600,
    ) -> None:
        self.api_key = api_key
        self.from_address = f"{from_name} <{from_email}>" if from_name else from_email
        self.otp_ttl_seconds = otp_ttl_seconds

    def _expires_in_label(self, seconds: int) -> str:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

    async def send_otp(self, to_email: str, otp: str) -> None:
        expires_in = self._expires_in_label(self.otp_ttl_seconds)
        html = f"""
        <div style="font-family:monospace;background:#0d0d0d;color:#d4d4d4;padding:40px;max-width:560px;margin:auto;border:1px solid #2a2a2a;">
          <div style="border-bottom:2px solid #7ed906;padding-bottom:16px;margin-bottom:24px;">
            <span style="color:#7ed906;font-size:13px;letter-spacing:4px;font-weight:700;">SMARTVAULT</span>
          </div>
          <p style="color:#555;font-size:9px;letter-spacing:3px;text-transform:uppercase;">ONE-TIME PASSCODE</p>
          <div style="background:#141414;border:1px solid #2a2a2a;padding:20px;text-align:center;margin-bottom:24px;">
            <span style="font-size:38px;font-weight:700;letter-spacing:12px;color:#7ed906;">{otp}</span>
          </div>
          <p style="color:#888;font-size:12px;line-height:1.7;">
            Enter this code to verify your identity. It expires in
            <span style="color:#d4d4d4;">{expires_in}</span>.
            Do not share it with anyone.
          </p>
          <div style="border-top:1px solid #1f1f1f;margin:24px 0;"></div>
          <p style="color:#555;font-size:11px;">
            If you did not request this code, someone may be attempting to access your account.
            Ignore this email — your vault remains locked.
          </p>
          <p style="color:#333;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-top:24px;">
            Sent to {to_email} · SmartVault Security System
          </p>
        </div>
        """
        payload = {
            "from": self.from_address,
            "to": [to_email],
            "subject": "Your SmartVault verification code",
            "html": html,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _RESEND_API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
        if response.status_code not in (200, 201):
            log.error("Resend send_otp failed: status=%s body=%s", response.status_code, response.text)
            raise RuntimeError(f"Resend error {response.status_code}: {response.text}")

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        payload = {
            "from": self.from_address,
            "to": [to_email],
            "subject": "Password reset for SmartVault",
            "html": f"""
            <div style="font-family:monospace;background:#0d0d0d;color:#d4d4d4;padding:40px;max-width:560px;margin:auto;border:1px solid #2a2a2a;">
              <div style="border-bottom:2px solid #7ed906;padding-bottom:16px;margin-bottom:24px;">
                <span style="color:#7ed906;font-size:13px;letter-spacing:4px;font-weight:700;">SMARTVAULT</span>
              </div>
              <p style="color:#555;font-size:9px;letter-spacing:3px;text-transform:uppercase;">Password Reset</p>
              <p style="color:#888;font-size:12px;line-height:1.7;">Use the token below to set a new password. It expires in 15 minutes.</p>
              <div style="background:#141414;border:1px solid #2a2a2a;padding:20px;word-break:break-all;margin-bottom:24px;">
                <span style="color:#7ed906;font-size:13px;">{token}</span>
              </div>
              <p style="color:#555;font-size:11px;">If you did not request this, ignore this email.</p>
            </div>
            """,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _RESEND_API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
        if response.status_code not in (200, 201):
            log.error("Resend send_password_reset_token failed: status=%s body=%s", response.status_code, response.text)
            raise RuntimeError(f"Resend error {response.status_code}: {response.text}")


class EmailJSEmailService:
    def __init__(
        self,
        *,
        service_id: str,
        template_id: str,
        public_key: str,
        private_key: str,
        otp_ttl_seconds: int = 600,
    ) -> None:
        self.service_id = service_id
        self.template_id = template_id
        self.public_key = public_key
        self.private_key = private_key
        self.otp_ttl_seconds = otp_ttl_seconds

    def _expires_in_label(self, seconds: int) -> str:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

    async def send_otp(self, to_email: str, otp: str) -> None:
        payload = {
            "service_id": self.service_id,
            "template_id": self.template_id,
            "user_id": self.public_key,
            "accessToken": self.private_key,
            "template_params": {
                "to_email": to_email,
                "otp": otp,
                "expires_in": self._expires_in_label(self.otp_ttl_seconds),
            },
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(_EMAILJS_API_URL, json=payload, timeout=10)
        if response.status_code != 200:
            log.error(
                "EmailJS send_otp failed: status=%s body=%s",
                response.status_code,
                response.text,
            )
            raise RuntimeError(f"EmailJS error {response.status_code}: {response.text}")

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        # EmailJS template not configured for password reset — log and skip.
        log.warning(
            "EmailJS send_password_reset_token not implemented; skipping for %s", to_email
        )


class DevEmailService:
    async def send_otp(self, to_email: str, otp: str) -> None:
        # Dev-only backend; mask OTP and log at debug level only.
        masked = otp[:2] + "*" * max(0, len(otp) - 2)
        log.debug("DEV EMAIL: sending masked OTP to %s code=%s", to_email, masked)

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        # Dev-only backend; mask token and log at debug level only.
        masked = token[:4] + "..." + token[-4:]
        log.debug("DEV EMAIL: sending masked reset token to %s token=%s", to_email, masked)


class SMTPEmailService:
    def __init__(
        self,
        *,
        host: str,
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        from_email: str,
        from_name: str | None = None,
        use_tls: bool = True,
    ) -> None:
        if aiosmtplib is None:
            raise RuntimeError("aiosmtplib is required for SMTPEmailService")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls

    async def send_otp(self, to_email: str, otp: str) -> None:
        assert aiosmtplib is not None, "SMTP backend not available"

        msg = EmailMessage()
        msg["From"] = (
            formataddr((self.from_name, self.from_email))
            if self.from_name
            else self.from_email
        )
        msg["To"] = to_email
        msg["Subject"] = "Your SmartVault verification code"
        msg.set_content(
            "Use the code below to finish signing in to SmartVault.\n\n"
            f"Code: {otp}\n"
            "If you did not request this code, you can ignore this email."
        )

        await aiosmtplib.send(
            message=msg,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            start_tls=self.use_tls,
        )

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        assert aiosmtplib is not None, "SMTP backend not available"

        msg = EmailMessage()
        msg["From"] = (
            formataddr((self.from_name, self.from_email))
            if self.from_name
            else self.from_email
        )
        msg["To"] = to_email
        msg["Subject"] = "Password reset for SmartVault"
        msg.set_content(
            "We received a request to reset your SmartVault password.\n"
            "Use the token below to set a new password:\n\n"
            f"Token: {token}\n\n"
            "This token will expire in 15 minutes.\n"
            "If you did not request a password reset, you can ignore this email."
        )

        await aiosmtplib.send(
            message=msg,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            start_tls=self.use_tls,
        )
