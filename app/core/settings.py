from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'Smart Vault API'
    environment: str = 'development'
    DEV_AUTH_BYPASS: bool = False
    DATABASE_URL: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/smartvault'
    REDIS_URL: str = 'redis://redis:6379/0'
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email / SMTP
    EMAIL_BACKEND: str | None = None  # "dev" or "smtp"
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str | None = None

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
