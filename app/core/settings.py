from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'Smart Vault API'
    environment: str = 'development'
    DEV_AUTH_BYPASS: bool = False
    DATABASE_URL: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/smartvault'
    REDIS_URL: str = 'redis://redis:6379/0'
    REDIS_TLS_URL: str | None = None
    CORS_ORIGINS: list[str] = []

    @model_validator(mode='after')
    def _normalize_urls(self) -> 'Settings':
        # Heroku sets DATABASE_URL as postgres:// but SQLAlchemy needs postgresql+psycopg://
        if self.DATABASE_URL.startswith('postgres://'):
            self.DATABASE_URL = self.DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
        elif self.DATABASE_URL.startswith('postgresql://'):
            self.DATABASE_URL = self.DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
        # Heroku Redis premium uses REDIS_TLS_URL
        if self.REDIS_TLS_URL:
            self.REDIS_URL = self.REDIS_TLS_URL
        return self
    
    # Security
    SECRET_KEY: str
    VAULT_COMMAND_SECRET: str = "changeme"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email / SMTP
    EMAIL_BACKEND: str | None = None  # "dev", "smtp", or "emailjs"
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str | None = None

    # EmailJS
    EMAILJS_SERVICE_ID: str | None = None
    EMAILJS_TEMPLATE_ID: str | None = None
    EMAILJS_PUBLIC_KEY: str | None = None
    EMAILJS_PRIVATE_KEY: str | None = None

    # Resend
    RESEND_API_KEY: str | None = None
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"
    RESEND_FROM_NAME: str = "SmartVault"

    # OTP + ticket
    OTP_TTL_SECONDS: int = 600          # 10 min
    SIGNUP_TICKET_TTL_SECONDS: int = 300 # 5 min
    PASSWORD_RESET_TTL_SECONDS: int = 900 # 15 min
    
    # Rate Limiting
    RATE_LIMIT_OTP_REQ_PER_MIN: int = 3
    RATE_LIMIT_LOGIN_REQ_PER_MIN: int = 5
    
    # SENTRY ERROR TRACKING
    SENTRY_DSN: str | None = Field(
        None,
        description="Sentry DSN for error tracking"
    )
    SENTRY_ENVIRONMENT: str = Field(
        "development",
        description="Environment name (development/staging/production)"
    )
    SENTRY_TRACES_SAMPLE_RATE: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Percentage of transactions to trace (0.0-1.0)"
    )
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Percentage of transactions to profile (0.0-1.0)"
    )
    SENTRY_SEND_DEFAULT_PII: bool = Field(
        False,
        description="Whether to send personally identifiable information (KEEP FALSE)"
    )
    
    # INTERNAL ADMIN API
    ADMIN_API_TOKEN: str | None = Field(
        None,
        description=(
            "Secret token for internal admin API. "
            "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    )
    
    @property
    def resolved_email_backend(self) -> str:
        """Choose email backend based on explicit setting, environment, and SMTP availability."""
        explicit = self.EMAIL_BACKEND.lower() if self.EMAIL_BACKEND else None
        if explicit:
            return explicit

        env = (self.environment or '').lower()
        if env == 'development' or not self.SMTP_HOST:
            return 'dev'
        return 'smtp'


settings = Settings()
