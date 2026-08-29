from __future__ import annotations

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import Settings, get_settings


class LlmNotConfigured(RuntimeError):
    pass


def require_llm(settings: Settings | None = None) -> Settings:
    settings = settings or get_settings()
    if not settings.llm_configured:
        raise LlmNotConfigured(
            "No LLM key found. Set FASTROUTER_API_KEY or OPENAI_API_KEY in the repo-root .env."
        )
    return settings


def chat_model(settings: Settings | None = None, temperature: float = 0) -> ChatOpenAI:
    settings = require_llm(settings)
    return ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.openai_compatible_key,
        base_url=settings.openai_compatible_base,
        temperature=temperature,
    )


def embedding_model(settings: Settings | None = None) -> OpenAIEmbeddings:
    settings = require_llm(settings)
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.embedding_key,
        base_url=settings.embedding_endpoint,
    )
