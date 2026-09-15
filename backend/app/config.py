from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql://nexusai:nexusai@localhost:5432/nexusai"

    # --- FROZEN BASELINE (Final V2, Member 5 amendments) ---
    # Do not change these without bumping SCORING_VERSION. Every score row
    # persists the version it was produced under so old rows stay explainable.
    SCORING_VERSION: str = "v1.0.0"

    # Gap priority = normalized_demand * trend_multiplier * gap_severity * role_importance
    GAP_DEMAND_WEIGHT: float = 1.0
    GAP_TREND_WEIGHT: float = 1.0
    GAP_SEVERITY_WEIGHT: float = 1.0
    GAP_IMPORTANCE_WEIGHT: float = 1.0

    # Match score baseline weights (must sum to 1.0)
    W_SKILL_COVERAGE: float = 0.60
    W_SEMANTIC: float = 0.20
    W_EXPERIENCE: float = 0.10
    W_EDUCATION: float = 0.05
    W_LOCATION: float = 0.05

    # Components considered "optional" for renormalization purposes.
    OPTIONAL_COMPONENTS: tuple = ("education", "location")


settings = Settings()

MATCH_WEIGHTS = {
    "skill_coverage": settings.W_SKILL_COVERAGE,
    "semantic": settings.W_SEMANTIC,
    "experience": settings.W_EXPERIENCE,
    "education": settings.W_EDUCATION,
    "location": settings.W_LOCATION,
}
