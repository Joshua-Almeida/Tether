from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    fastrouter_api_url: str = "https://api.fastrouter.ai/api/v1"
    fastrouter_api_key: str = ""
    fastrouter_llm_model: str = "openai/gpt-4o-mini"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    embedding_model: str = "text-embedding-3-small"
    embedding_base_url: str = ""
    embedding_api_key: str = ""

    api_host: str = "127.0.0.1"
    api_port: int = 8765
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    chroma_dir: str = str(BACKEND_DIR / "data" / "chroma")
    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieve_k: int = 6
    retrieve_mode: str = "hybrid"
    rewrite_max: int = 1
    grade_relevance_threshold: float = 0.5

    @property
    def llm_configured(self) -> bool:
        return bool(self.fastrouter_api_key or self.openai_api_key)

    @property
    def chat_model(self) -> str:
        if self.fastrouter_api_key:
            return self.fastrouter_llm_model
        return self.openai_model

    @property
    def openai_compatible_base(self) -> str:
        if self.fastrouter_api_key:
            return self.fastrouter_api_url.rstrip("/")
        return self.openai_base_url.rstrip("/")

    @property
    def openai_compatible_key(self) -> str:
        if self.fastrouter_api_key:
            return self.fastrouter_api_key
        return self.openai_api_key

    @property
    def embedding_endpoint(self) -> str:
        if self.embedding_base_url.strip():
            return self.embedding_base_url.rstrip("/")
        return self.openai_compatible_base

    @property
    def embedding_key(self) -> str:
        if self.embedding_api_key.strip():
            return self.embedding_api_key
        return self.openai_compatible_key

    @property
    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]

    @property
    def chroma_path(self) -> Path:
        path = Path(self.chroma_dir)
        if not path.is_absolute():
            path = ROOT / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
