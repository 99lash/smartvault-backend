from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Smart Vault API"
    environment: str = "development"


settings = Settings()
