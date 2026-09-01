from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "ai-agentic-document-intelligence"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    upload_dir: str = str(BASE_DIR / "data" / "uploads")
    index_dir: str = str(BASE_DIR / "data" / "indexes")
    max_upload_size_mb: int = 20
    allowed_extensions: set[str] = {"pdf", "txt", "csv", "xlsx", "xls"}
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


settings = Settings()
