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

    # Member 5 scoring configuration
    MATCH_SKILL_WEIGHT: float = 0.60
    MATCH_SEMANTIC_WEIGHT: float = 0.20
    MATCH_EXPERIENCE_WEIGHT: float = 0.10
    MATCH_EDUCATION_WEIGHT: float = 0.05
    MATCH_LOCATION_MODE_WEIGHT: float = 0.05

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()