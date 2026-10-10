import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from OMVERSION directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "storage" / "data"
    STORAGE_ROOT: Path = Path(os.getenv("STORAGE_ROOT", str(BASE_DIR / "storage" / "media")))

    # Resolve DATABASE_URL safely to absolute path if SQLite
    raw_db_url = os.getenv("DATABASE_URL", "")
    if not raw_db_url or "sqlite" in raw_db_url:
        # Guarantee absolute path inside OMVERSION/storage/data/
        db_file = BASE_DIR / "storage" / "data" / "microdrama.db"
        DATABASE_URL: str = f"sqlite:///{db_file}"
    else:
        DATABASE_URL: str = raw_db_url

    def _get_val(key: str, default: str = "") -> str:
        v = os.getenv(key)
        if not v:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and key in st.secrets:
                    v = str(st.secrets[key])
            except Exception:
                pass
        return v or default

    LLM_PROVIDER: str = _get_val("LLM_PROVIDER", "cloudflare")
    LLM_API_KEY: str = _get_val("LLM_API_KEY", "")
    LLM_MODEL: str = _get_val("LLM_MODEL", "@cf/google/gemma-4-26b-a4b-it")
    GEMINI_API_KEY: str = _get_val("GEMINI_API_KEY", _get_val("LLM_API_KEY", ""))

    CLOUDFLARE_ACCOUNT_ID: str = _get_val("CLOUDFLARE_ACCOUNT_ID", "")
    CLOUDFLARE_AUTH_TOKEN: str = _get_val("CLOUDFLARE_AUTH_TOKEN", "")

    MODAL_APP_NAME: str = _get_val("MODAL_APP_NAME", "microdrama-studio-workers")
    MODAL_ENVIRONMENT: str = _get_val("MODAL_ENVIRONMENT", "main")
    STUDIO_PASSWORD: str = _get_val("STUDIO_PASSWORD", "")

    DEFAULT_FPS: int = int(_get_val("DEFAULT_FPS", "24"))
    DEFAULT_RESOLUTION: str = _get_val("DEFAULT_RESOLUTION", "1080p")
    DEFAULT_ASPECT_RATIO: str = _get_val("DEFAULT_ASPECT_RATIO", "16:9")

    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
