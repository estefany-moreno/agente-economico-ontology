"""
Factory de LLM segun LLM_PROVIDER (plan secciones 4-5).

Proveedores: groq (default) | gemini | openrouter.
Las API keys viven solo en variables de entorno; nunca en el codigo.
"""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel

# Reintentos HTTP del cliente (429/5xx). Gemini trae 6 por defecto: en tier
# gratuito cada reintento consume cuota del mismo minuto, asi que se acota.
MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "2"))


# Respaldo de Groq cuando el modelo principal agota su cuota (agent/fallback.py).
# Groq limita cada modelo por separado. Vacio = sin respaldo.
GROQ_FALLBACK_DEFAULT = "openai/gpt-oss-20b"


def _chat_groq(model: str, max_retries: int) -> BaseChatModel:
    """ChatGroq con los ajustes del proyecto."""
    from langchain_groq import ChatGroq

    extra = {}
    if "gpt-oss" in model:
        # Menos tokens de razonamiento -> menos consumo del limite TPM de Groq
        extra["reasoning_effort"] = os.environ.get("GROQ_REASONING_EFFORT", "low")
    return ChatGroq(
        model=model,
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0,
        max_retries=max_retries,
        **extra,
    )


def get_fallback_llm() -> BaseChatModel | None:
    """
    Modelo de respaldo (solo Groq): GROQ_FALLBACK_MODEL, por defecto gpt-oss-20b.
    None si el proveedor no es Groq, si se desactivo (GROQ_FALLBACK_MODEL=) o si
    coincide con el modelo principal.
    """
    if os.environ.get("LLM_PROVIDER", "groq").strip().lower() != "groq":
        return None
    respaldo = os.environ.get("GROQ_FALLBACK_MODEL", GROQ_FALLBACK_DEFAULT).strip()
    principal = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b").strip()
    if not respaldo or respaldo == principal:
        return None
    return _chat_groq(respaldo, MAX_RETRIES)


def get_llm() -> BaseChatModel:
    """
    Devuelve el chat model configurado por LLM_PROVIDER.
    - groq: GROQ_API_KEY
    - gemini: GOOGLE_API_KEY
    - openrouter: OPENROUTER_API_KEY (cliente OpenAI-compatible)
    """
    provider = os.environ.get("LLM_PROVIDER", "groq").strip().lower()

    if provider == "groq":
        # Default del plan: baja latencia y tool-calling confiable.
        # Con respaldo configurado, el principal no reintenta ante 429: es mejor
        # pasar de inmediato al respaldo que esperar y gastar requests fallidas.
        con_respaldo = get_fallback_llm() is not None
        return _chat_groq(
            os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
            0 if con_respaldo else MAX_RETRIES,
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=os.environ["GOOGLE_API_KEY"],
            temperature=0,
            max_retries=MAX_RETRIES,
        )

    if provider == "openrouter":
        # OpenRouter usa API compatible con OpenAI
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.environ.get("OPENROUTER_MODEL", "openrouter/auto"),
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
            max_retries=MAX_RETRIES,
        )

    raise ValueError(
        f"LLM_PROVIDER desconocido: {provider!r}. Use groq | gemini | openrouter."
    )
