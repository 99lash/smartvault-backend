from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Smart Vault API"
    environment: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/smartvault"
    REDIS_URL: str = "redis://redis:6379/0"

    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/smartvault"
    )

    class Config:
        env_file = ".env"


settings = Settings()
