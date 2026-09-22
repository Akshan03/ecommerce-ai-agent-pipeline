"""
Configuration management module.
Loads environment variables and defines project-wide constants and paths.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    # LLM Providers (Defaults to empty strings if not found)
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    # Application settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT_SECONDS: int = 30
    IMAGE_GENERATION_LIMIT: int = 3
    
    # Directory Paths
    DATA_DIR: Path = BASE_DIR / "data"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    CONTENT_DIR: Path = OUTPUT_DIR / "content"
    IMAGES_DIR: Path = OUTPUT_DIR / "images"
    REPORTS_DIR: Path = OUTPUT_DIR / "reports"

# Instantiate settings to be imported across the project
settings = Settings()