import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from OMVERSION directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    BASE_DIR: Path = BASE_DIR
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/storage/data/microdrama.db")
    STORAGE_ROOT: Path = Path(os.getenv("STORAGE_ROOT", str(BASE_DIR / "storage" / "media")))
    DATA_DIR: Path = BASE_DIR / "storage" / "data"

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "cloudflare")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "@cf/google/gemma-4-26b-a4b-it")

    CLOUDFLARE_ACCOUNT_ID: str = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    CLOUDFLARE_AUTH_TOKEN: str = os.getenv("CLOUDFLARE_AUTH_TOKEN", "")

    MODAL_APP_NAME: str = os.getenv("MODAL_APP_NAME", "microdrama-studio-workers")
    MODAL_ENVIRONMENT: str = os.getenv("MODAL_ENVIRONMENT", "main")

    DEFAULT_FPS: int = int(os.getenv("DEFAULT_FPS", "24"))
    DEFAULT_RESOLUTION: str = os.getenv("DEFAULT_RESOLUTION", "1080p")
    DEFAULT_ASPECT_RATIO: str = os.getenv("DEFAULT_ASPECT_RATIO", "16:9")

    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
