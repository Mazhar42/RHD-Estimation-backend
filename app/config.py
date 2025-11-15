import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=f".env.{os.getenv('APP_ENV', 'development')}", extra="ignore")

    # App settings
    APP_ENV: str = "development"

    # Database settings
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "estimation.db"
    DATABASE_URL: str = "sqlite:///./estimation.db"


settings = Settings()
