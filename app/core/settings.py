from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Smart Vault API"
    environment: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/smartvault"


settings = Settings()
