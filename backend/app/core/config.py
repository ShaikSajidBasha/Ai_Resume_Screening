"""
Centralized application configuration.
Loads all environment-dependent settings from .env — nothing here is hardcoded.
"""
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- AI ---
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
    AI_TIMEOUT_SECONDS: int = int(os.getenv("AI_TIMEOUT_SECONDS", "30"))
    AI_MAX_RETRIES: int = int(os.getenv("AI_MAX_RETRIES", "2"))

    # --- Database ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/resume_screening_db"
    )

    # --- Auth ---
    JWT_SECRET: str = os.getenv("JWT_SECRET", "insecure-dev-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # --- CORS ---
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # --- Uploads ---
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
    ALLOWED_RESUME_EXTENSIONS: tuple = (".pdf", ".docx", ".txt")

    # --- Scoring weights (must sum to 1.0). Configurable, not hardcoded in agents. ---
    SCORE_WEIGHTS: dict = {
        "ats_score": 0.25,
        "skill_score": 0.30,
        "keyword_score": 0.15,
        "experience_score": 0.15,
        "education_score": 0.10,
        "resume_quality_score": 0.05,
    }

    # --- Status thresholds (overall_score >= threshold -> label), evaluated top-down ---
    STATUS_THRESHOLDS: list = [
        (85, "Strong Match"),
        (65, "Moderate Match"),
        (45, "Needs Improvement"),
        (0, "Low Match"),
    ]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
