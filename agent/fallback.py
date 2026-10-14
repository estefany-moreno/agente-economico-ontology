"""
Cambio automatico a un modelo de respaldo cuando el principal agota su cuota.

Groq limita cada modelo por separado (tokens por minuto y por dia), asi que si
openai/gpt-oss-120b se queda sin cuota, openai/gpt-oss-20b sigue disponible.

A diferencia de ModelFallbackMiddleware de LangChain (que cambia ante CUALQUIER
error y reintenta el principal en cada llamada), este middleware:
- solo cambia ante un 429 (limite de cuota); otros errores se propagan,
- recuerda hasta cuando esta bloqueado el principal (Groq lo dice en el error:
  "Please try again in 21m24.3s") y mientras tanto va directo al respaldo,
  sin gastar una request fallida por cada pregunta.
"""

from __future__ import annotations

import logging
import re
import time

from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models.chat_models import BaseChatModel

log = logging.getLogger(__name__)

# Espera por defecto si el error no indica cuanto falta para liberar la cuota
ESPERA_DEFAULT_S = 60.0


def es_limite_de_cuota(exc: BaseException) -> bool:
    """True si el proveedor respondio 429 (rate limit / cuota agotada)."""
    if type(exc).__name__ in ("RateLimitError", "GoogleRateLimitError"):
        return True
    codigo = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    return codigo == 429


def segundos_de_espera(exc: BaseException) -> float:
    """Lee "try again in 1h2m3.5s" / "21m24.3s" / "2.1s" del mensaje de Groq."""
    m = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?", str(exc))
    if not m or not any(m.groups()):
        return ESPERA_DEFAULT_S
    h, mi, s = (float(g) if g else 0.0 for g in m.groups())
    return h * 3600 + mi * 60 + s


class FallbackPorCuotaMiddleware(AgentMiddleware):
    """Usa `respaldo` cuando el modelo principal responde 429."""

    def __init__(self, respaldo: BaseChatModel):
        super().__init__()
        self.respaldo = respaldo
        # Momento (time.time()) hasta el que no conviene usar el principal.
        # Compartido por todas las preguntas del proceso (CLI o app Streamlit).
        self._principal_bloqueado_hasta = 0.0

    def wrap_model_call(self, request, handler):
        # Principal en "enfriamiento": ir directo al respaldo
        if time.time() < self._principal_bloqueado_hasta:
            return handler(request.override(model=self.respaldo))

        try:
            return handler(request)
        except Exception as exc:
            if not es_limite_de_cuota(exc):
                raise  # errores que no son de cuota no se ocultan
            espera = segundos_de_espera(exc)
            self._principal_bloqueado_hasta = time.time() + espera
            log.warning(
                "Modelo principal sin cuota (%s); usando respaldo durante %.0f s.",
                type(exc).__name__,
                espera,
            )
            # create_agent vuelve a enlazar las tools al modelo de respaldo
            return handler(request.override(model=self.respaldo))
