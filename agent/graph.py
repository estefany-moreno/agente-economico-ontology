"""
Orquestacion del agente con create_agent (LangChain 1.x / LangGraph).

Plan seccion 4: tool-calling loop con OntoRank + APIs + noticias + graficas.
Middleware: contexto OntoRank precalculado (sin LLM) + resumen de historial
largo + redaccion de PII (email) + tope de llamadas al LLM por pregunta
+ reintento si el LLM inventa un nombre de tool invalido.
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelCallLimitMiddleware,
    ModelRetryMiddleware,
    PIIMiddleware,
    SummarizationMiddleware,
    ToolErrorMiddleware,
)
from langchain_core.messages import HumanMessage

from agent.fallback import FallbackPorCuotaMiddleware
from agent.llm import get_fallback_llm, get_llm
from agent.tools.banxico_tool import consultar_banxico
from agent.tools.chart_tool import generar_grafica
from agent.tools.errores import ErrorDeFuente
from agent.tools.inegi_tool import consultar_inegi
from agent.tools.news_sheets_tool import consultar_noticias
from agent.tools.ontorank_tool import buscar_indicador_relevante, contexto_ontorank

# Tope de llamadas al LLM por pregunta (corta loops de tool-calling)
MAX_LLM_CALLS = int(os.environ.get("MAX_LLM_CALLS", "5"))

# Instrucciones del analista (plan seccion 4, puntos 1-4), redactadas para
# resolver una pregunta tipica en 2 llamadas al LLM: (1) pedir datos (+ grafica
# con graficar=True), (2) redactar la respuesta.
PROMPT_ANALISTA_ECONOMICO = """\
Eres un analista economico de Mexico. Respondes en espanol, con rigor y citando fuentes.
Usa solo estos nombres exactos de tools: buscar_indicador_relevante, consultar_inegi, \
consultar_banxico, consultar_noticias, generar_grafica.

Reglas:
1. Cada pregunta trae un bloque [OntoRank] con los indicadores de la ontologia mas \
relevantes (fuente, claveAPI, unidad, frecuencia). Usalo directamente; llama a \
buscar_indicador_relevante solo si ninguno de esos indicadores sirve.
2. Datos: consultar_inegi si fuente=INEGI, consultar_banxico si fuente=Banxico, con \
serie_id=claveAPI. Si claveAPI esta vacia, dilo y no inventes un ID.
3. Las tools de datos devuelven un resumen ya calculado (ultimo valor, variaciones, \
max/min, ultimas observaciones). Citalo tal cual; no inventes ni recalcules cifras. \
Respeta unidad y frecuencia.
4. Si una visualizacion aporta (tendencias, series), pasa graficar=True (y un titulo) \
a consultar_inegi/consultar_banxico: obtiene datos y grafica en la misma llamada. \
Usa generar_grafica solo para regraficar una serie ya consultada con otro rango o tipo.
5. Eficiencia: pide en UN SOLO turno todas las tools que no dependan entre si \
(p. ej. varias series a la vez). No repitas una consulta que ya tienes.
6. Noticias/sentimiento: consultar_noticias; para un mes o periodo pasa fecha_ini y \
fecha_fin (usa la fecha de hoy del contexto para inferir el año). Cita el resumen \
agregado tal cual.
7. Cita siempre la fuente. Nunca pidas ni expongas tokens ni credenciales.
"""


class OntoRankContextMiddleware(AgentMiddleware):
    """
    Antes de la primera llamada al modelo, corre OntoRank localmente y anexa el
    top-k a la pregunta. Ahorra el turno de LLM que solo servia para invocar
    buscar_indicador_relevante (que sigue disponible como tool, plan seccion 0).
    """

    def before_agent(self, state, runtime) -> dict[str, Any] | None:
        ultimo = next(
            (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            None,
        )
        if ultimo is None or not isinstance(ultimo.content, str):
            return None
        if "[OntoRank" in ultimo.content:
            return None
        # Fecha de hoy: el modelo la necesita para traducir "abril" o "el mes
        # pasado" a fechas concretas (no va en el system prompt porque la app
        # Streamlit construye el agente una sola vez y quedaria desactualizada)
        contexto = f"[Fecha de hoy: {date.today().isoformat()}]\n" + contexto_ontorank(ultimo.content)
        # Mismo id -> add_messages reemplaza el mensaje en lugar de duplicarlo
        return {
            "messages": [
                HumanMessage(content=f"{ultimo.content}\n\n{contexto}", id=ultimo.id)
            ]
        }


def _reintentar_si_tool_invalida(exc: BaseException) -> bool:
    """
    True si Groq/el proveedor rechazo un tool call por nombre inexistente
    (typo del LLM). Otros 400 permanentes no se reintentan aqui.
    """
    msg = str(exc).lower()
    return (
        "tool_use_failed" in msg
        or "tool call validation failed" in msg
        or "which was not in request.tools" in msg
    )


def _error_de_tool_para_el_modelo(exc: Exception, request: Any = None) -> str:
    """
    Convierte la falla de una tool en un ToolMessage de error, en vez de tumbar
    toda la ejecucion: asi el agente le explica al usuario que fuente fallo.
    Solo ErrorDeFuente expone su mensaje; del resto se reporta el tipo (su texto
    podria incluir URLs con tokens).
    """
    if isinstance(exc, ErrorDeFuente):
        detalle = str(exc)
    else:
        detalle = f"fallo interno ({type(exc).__name__})"
    return f"ERROR de la herramienta: {detalle} Informa al usuario; no reintentes la misma llamada."


def build_agent():
    """
    Construye el grafo del agente (CompiledStateGraph) con las 5 tools y
    middleware: contexto OntoRank + resumen + PII + tope de llamadas + reintento
    + manejo de errores de tools + respaldo de modelo por cuota.
    """
    model = get_llm()

    # Resumen solo si el historial crece de verdad: las tools ya devuelven
    # resumenes compactos, asi que un umbral bajo solo gastaria llamadas extra
    summarization = SummarizationMiddleware(
        model,
        trigger=("tokens", 12000),
        keep=("messages", 20),
    )
    # Redaccion de PII basica (email); los tokens de API no deben llegar al prompt
    pii_email = PIIMiddleware("email", strategy="redact", apply_to_input=True)
    # Tope duro de llamadas al LLM por pregunta; al llegar, termina el loop
    call_limit = ModelCallLimitMiddleware(run_limit=MAX_LLM_CALLS, exit_behavior="end")
    # Errores de tools -> mensaje al modelo (no excepcion que corte la respuesta)
    tool_errors = ToolErrorMiddleware(on_error=_error_de_tool_para_el_modelo)
    # Reintenta la llamada al modelo si invento un nombre de tool (ej. consultar_bancio)
    model_retry = ModelRetryMiddleware(
        max_retries=1,
        retry_on=_reintentar_si_tool_invalida,
        initial_delay=0.5,
        backoff_factor=2.0,
        on_failure="error",  # si agota reintentos, propaga el error
    )

    middleware = [
        OntoRankContextMiddleware(),
        summarization,
        pii_email,
        call_limit,
        model_retry,
        tool_errors,
    ]
    # Respaldo automatico si el modelo principal de Groq agota su cuota (429)
    respaldo = get_fallback_llm()
    if respaldo is not None:
        middleware.append(FallbackPorCuotaMiddleware(respaldo))

    return create_agent(
        model=model,
        tools=[
            buscar_indicador_relevante,
            consultar_banxico,
            consultar_inegi,
            consultar_noticias,
            generar_grafica,
        ],
        system_prompt=PROMPT_ANALISTA_ECONOMICO,
        middleware=middleware,
    )
