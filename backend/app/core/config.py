from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "NexusAI API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    TAXONOMY_VERSION: str = "v1.2.1"
    RESUME_STORAGE_DIR: str = "storage/resumes"
    PROCESSED_DATA_DIR: str = "datasets/processed"

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @model_validator(mode="after")
    def reject_production_placeholder_secret(self) -> "Settings":
        placeholders = {
            "your-secret-key-here",
            "replace-with-a-long-random-jwt-signing-secret",
            "change-me",
            "secret",
            "jwt-secret",
        }
        if (
            self.ENVIRONMENT.casefold() != "development"
            and self.JWT_SECRET_KEY.strip().casefold() in placeholders
        ):
            raise ValueError("JWT_SECRET_KEY must not use a placeholder outside development")
        if "*" in self.BACKEND_CORS_ORIGINS:
            raise ValueError("BACKEND_CORS_ORIGINS must not include '*' when credentials are enabled")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
