"""
core/config.py — Application configuration using Pydantic Settings
"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator

_BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────
    app_name: str = "Resume match anaalyzer by zayeem"
    version: str = "1.0.0"
    debug: bool = Field(default=False)
    log_level: str = "INFO"

    # ── Paths ──────────────────────────────────────────────────
    base_dir: Path = _BASE_DIR
    upload_dir: Optional[Path] = None
    data_dir: Optional[Path] = None
    db_path: str = Field(default="sqlite+aiosqlite:///./resume_analyzer.db")

    # ── NLP Models ─────────────────────────────────────────────
    sbert_model: str = "all-MiniLM-L6-v2"
    bert_model: str = "bert-base-uncased"
    spacy_model: str = "en_core_web_sm"

    # ── Score Weights (must sum to 1.0) ────────────────────────
    tfidf_weight: float = 0.25
    sbert_weight: float = 0.55
    bert_weight: float = 0.20

    # ── LLM ────────────────────────────────────────────────────
    openai_api_key: str = Field(default="")
    openai_model: str = "gpt-3.5-turbo"
    use_llm: bool = Field(default=False)

    # ── Kaggle ─────────────────────────────────────────────────
    kaggle_username: str = Field(default="")
    kaggle_key: str = Field(default="")

    # ── CORS ────────────────────────────────────────────────────
    allowed_origins: list[str] = ["http://localhost:8501", "http://localhost:3000", "*"]

    @model_validator(mode="after")
    def _set_default_paths(self) -> "Settings":
        if self.upload_dir is None:
            self.upload_dir = self.base_dir / "uploads"
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "data" / "processed").mkdir(parents=True, exist_ok=True)
        return self

    @property
    def effective_use_llm(self) -> bool:
        return bool(self.openai_api_key) and self.use_llm


settings = Settings()
