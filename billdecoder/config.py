"""Configuration module for WTQ Utility Bill Decoder."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

ALLOWED_MODELS = {"gemini-3.5-flash-lite", "gemini-3.1-flash-lite"}
DEFAULT_MODEL = "gemini-3.5-flash-lite"
PROMPT_VERSION = "1.2.1"


class Settings:
    """Application settings with strict validation."""

    def __init__(self) -> None:
        self.model_provider: str = os.getenv("MODEL_PROVIDER", "google").strip().lower()
        self.model_name: str = os.getenv("MODEL_NAME", DEFAULT_MODEL).strip()
        
        # Read API key from env (supports both API_KEY and GEMINI_API_KEY)
        self.api_key: Optional[str] = (
            os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY")
        )
        if self.api_key:
            self.api_key = self.api_key.strip()
            
        # Global rate limit: requests per minute (default <= 10)
        self.rate_limit_rpm: int = int(os.getenv("RATE_LIMIT_RPM", "10"))
        
        # Concurrency limit (default 1 to be conservative with free tier)
        self.max_concurrency: int = int(os.getenv("MAX_CONCURRENCY", "1"))
        
        # Disk cache settings (use /tmp on serverless environments where working dir is read-only)
        default_cache = "/tmp/.cache/billdecoder" if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")) else ".cache/billdecoder"
        cache_dir_env = os.getenv("CACHE_DIR", default_cache)
        self.cache_dir: Path = Path(cache_dir_env)
        self.cache_enabled: bool = os.getenv("DISABLE_CACHE", "0") != "1"
        
        # Max image dimension
        self.max_image_dimension: int = 2048
        self.max_upload_bytes: int = 15 * 1024 * 1024  # 15 MB

    def validate_or_raise(self) -> None:
        """Enforces hard rules on configuration."""
        if self.model_name not in ALLOWED_MODELS:
            raise ValueError(
                f"Disallowed model: '{self.model_name}'. "
                f"Strict competition rule: Only 'gemini-3.5-flash-lite' (or 'gemini-3.1-flash-lite' if explicitly permitted) is allowed."
            )
        if not self.api_key:
            raise ValueError(
                "Missing API key. Set API_KEY (or GEMINI_API_KEY) in your environment or .env file."
            )


# Global settings singleton
settings = Settings()
