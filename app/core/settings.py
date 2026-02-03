from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Smart Vault API"
    environment: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/smartvault"
    REDIS_URL: str = "redis://redis:6379/0"

    # OTP + ticket
    OTP_TTL_SECONDS: int = 600          # 10 min
    SIGNUP_TICKET_TTL_SECONDS: int = 300 # 5 min

settings = Settings()
