"""
Interfaz web del agente economico con Streamlit.

Uso (desde la raiz del repo, con el environment activo y .env lleno):
    streamlit run app.py

Estructura de la pagina:
- Encabezado con degradado.
- Panel de indicadores clave (metricas con mini-grafica), calculado en Python
  directo de INEGI/Banxico: no gasta llamadas al LLM.
- Chat con el agente: muestra las tools que va usando, la respuesta y las
  graficas Plotly interactivas que pidio.
- Sidebar: preguntas de ejemplo, proveedor LLM y boton para reiniciar.
"""

from __future__ import annotations

import os

# .env debe cargarse ANTES de importar el agente: agent.graph lee
# MAX_LLM_CALLS y agent.llm lee LLM_PROVIDER al importarse/construirse
from dotenv import load_dotenv

load_dotenv()

import pandas as pd
import streamlit as st
from langchain_core.messages import AIMessage, ToolMessage

from agent.fallback import es_limite_de_cuota
from agent.formato import formatear_respuesta
from agent.graph import build_agent
from agent.llm import GROQ_FALLBACK_DEFAULT
from agent.tools.chart_tool import figura_serie
from agent.tools.ontorank_tool import _get_ranker
from agent.tools.series_cache import obtener_serie

# ---------------------------------------------------------------------------
# Configuracion general de la pagina (debe ser la primera llamada a st.*)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Agente Económico MX",
    page_icon="📈",
    layout="wide",
)

# Turnos previos (pregunta + respuesta) que se reenvian al agente para que
# entienda seguimientos como "¿y hace dos años?". Pocos = menos tokens.
TURNOS_DE_CONTEXTO = 2

# Panel de metricas: series de la ontologia que se muestran arriba.
#   calculo = "nivel"     -> ultimo valor de la serie
#   calculo = "var_anual" -> variacion % anual (serie mensual, 12 periodos)
#   delta   = "previo"    -> cambio vs la observacion anterior
#   delta   = "anual"     -> cambio vs hace un año
#   delta_color "inverse" -> subir se pinta en rojo (p. ej. inflacion)
PANEL = [
    {"label": "Inflación anual (INPC)", "fuente": "INEGI", "serie_id": "910392",
     "calculo": "var_anual", "delta": "previo", "fmt": "{:.2f}%", "delta_fmt": "{:+.2f} pp",
     "delta_color": "inverse", "delta_desc": "vs. mes anterior"},
    {"label": "Tasa objetivo Banxico", "fuente": "Banxico", "serie_id": "SF61745",
     "calculo": "nivel", "delta": "anual", "fmt": "{:.2f}%", "delta_fmt": "{:+.2f} pp",
     "delta_color": "inverse", "delta_desc": "vs. hace un año"},
    {"label": "Tipo de cambio FIX", "fuente": "Banxico", "serie_id": "SF43718",
     "calculo": "nivel", "delta": "previo", "fmt": "${:.4f}", "delta_fmt": "{:+.4f}",
     "delta_color": "inverse", "delta_desc": "vs. día anterior"},
    {"label": "TIIE a 28 días", "fuente": "Banxico", "serie_id": "SF43783",
     "calculo": "nivel", "delta": "anual", "fmt": "{:.2f}%", "delta_fmt": "{:+.2f} pp",
     "delta_color": "inverse", "delta_desc": "vs. hace un año"},
    {"label": "IGAE (var. anual)", "fuente": "INEGI", "serie_id": "737219",
     "calculo": "var_anual", "delta": "previo", "fmt": "{:.2f}%", "delta_fmt": "{:+.2f} pp",
     "delta_color": "normal", "delta_desc": "vs. mes anterior"},
    {"label": "Tasa de desocupación", "fuente": "INEGI", "serie_id": "444884",
     "calculo": "nivel", "delta": "anual", "fmt": "{:.2f}%", "delta_fmt": "{:+.2f} pp",
     "delta_color": "inverse", "delta_desc": "vs. hace un año"},
]

# Etiquetas amigables para mostrar el progreso de cada tool en el chat
NOMBRES_TOOLS = {
    "buscar_indicador_relevante": "🧭 Buscando indicadores en la ontología",
    "consultar_inegi": "📊 Consultando INEGI",
    "consultar_banxico": "🏦 Consultando Banxico",
    "consultar_noticias": "📰 Leyendo noticias y sentimiento",
    "generar_grafica": "📈 Generando gráfica",
}

PREGUNTAS_EJEMPLO = [
    "¿Cómo va la inflación? Grafica la serie.",
    "¿Cómo ha evolucionado el tipo de cambio en el último año?",
    "Compara la tasa objetivo de Banxico con la TIIE a 28 días.",
    "¿Cómo va la producción industrial?",
    "¿Cuál fue el tono de las noticias económicas en abril?",
]

# ---------------------------------------------------------------------------
# Estilos extra (CSS): encabezado con degradado y tarjetas de metricas.
# El resto del look (colores, fuentes, sidebar) esta en .streamlit/config.toml
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .hero {
        background: linear-gradient(120deg, #0F766E 0%, #1E3A8A 55%, #4F46E5 100%);
        color: #FFFFFF;
        padding: 1.6rem 2rem;
        border-radius: 1rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 30px rgba(30, 58, 138, 0.25);
    }
    .hero h1 { color: #FFFFFF; margin: 0; font-size: 2.1rem; }
    .hero p  { color: #DCE7F7; margin: .4rem 0 0 0; font-size: 1.02rem; }
    /* Tarjetas de metricas: fondo blanco y sombra suave */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }
    </style>
    <div class="hero">
        <h1>📈 Agente Económico de México</h1>
        <p>Pregunta en lenguaje natural: el agente ubica el indicador en la ontología
        (OntoRank), consulta INEGI / Banxico / noticias y responde citando la fuente.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Recursos pesados: se crean UNA vez por servidor (no en cada interaccion).
# st.cache_resource mantiene el objeto vivo entre reruns y usuarios, asi el
# modelo de Hugging Face y el grafo del agente se cargan una sola vez.
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Cargando el agente y el modelo de embeddings...")
def obtener_agente():
    _get_ranker()  # precarga OntoRank (sentence-transformers) para no esperar en la 1a pregunta
    return build_agent()


# ---------------------------------------------------------------------------
# Panel de metricas: calculos en pandas, sin LLM. st.cache_data guarda el
# resultado 6 h, asi recargar la pagina no vuelve a pegarle a las APIs.
# ---------------------------------------------------------------------------
def _valor_hace_un_anio(s: pd.Series) -> float | None:
    """Ultimo valor con fecha <= (ultima fecha - 1 año)."""
    base = s[s.index <= s.index[-1] - pd.DateOffset(years=1)]
    return float(base.iloc[-1]) if len(base) else None


@st.cache_data(ttl=6 * 3600, show_spinner="Actualizando indicadores...")
def cargar_panel() -> list[dict]:
    tarjetas = []
    for ind in PANEL:
        try:
            df = obtener_serie(ind["fuente"], ind["serie_id"]).dropna(subset=["valor"])
            s = df.set_index("fecha")["valor"]
            # Serie que se muestra: el nivel o su variacion anual en %
            if ind["calculo"] == "var_anual":
                s = (s.pct_change(12) * 100).dropna()
            actual = float(s.iloc[-1])
            if ind["delta"] == "previo":
                referencia = float(s.iloc[-2]) if len(s) > 1 else None
            else:
                referencia = _valor_hace_un_anio(s)
            tarjetas.append(
                {
                    **ind,
                    "valor": actual,
                    "cambio": None if referencia is None else actual - referencia,
                    "fecha": s.index[-1].strftime("%Y-%m-%d"),
                    # Mini-grafica: ultimos 24 puntos (60 si la serie es diaria)
                    "spark": s.tail(60 if len(s) > 2000 else 24).round(4).tolist(),
                }
            )
        except Exception as exc:  # una API caida no debe tumbar toda la pagina
            tarjetas.append({**ind, "error": str(exc)[:120]})
    return tarjetas


def mostrar_panel() -> None:
    st.subheader("Indicadores clave")
    tarjetas = cargar_panel()
    # 3 columnas x 2 filas: legible en laptop y en pantallas anchas
    columnas = st.columns(3)
    for i, t in enumerate(tarjetas):
        with columnas[i % 3]:
            if "error" in t:
                st.metric(t["label"], "N/D", border=True, help=f"No disponible: {t['error']}")
                continue
            st.metric(
                label=t["label"],
                value=t["fmt"].format(t["valor"]),
                delta=None if t["cambio"] is None else t["delta_fmt"].format(t["cambio"]),
                delta_color=t["delta_color"],
                delta_description=t["delta_desc"],
                chart_data=t["spark"],
                chart_type="area",
                border=True,
                help=f"Fuente: {t['fuente']}, serie {t['serie_id']}. Último dato: {t['fecha']}",
            )


# ---------------------------------------------------------------------------
# Graficas: se reconstruyen desde la cache de series con el estilo fijo del
# proyecto (chart_tool._fig) y se muestran interactivas con st.plotly_chart.
# Se guarda solo la "receta" (fuente, serie, rango) en el historial, no la figura.
# ---------------------------------------------------------------------------
def mostrar_grafica(spec: dict, key: str) -> None:
    try:
        fig = figura_serie(**spec)
    except Exception as exc:
        st.warning(f"No se pudo dibujar la gráfica: {exc}")
        return
    # El estilo base fija 900 px de ancho; aqui se deja que ocupe el contenedor
    fig.update_layout(width=None, autosize=True)
    st.plotly_chart(fig, theme=None, key=key)  # theme=None respeta el estilo propio


def _spec_grafica(nombre_tool: str, args: dict) -> dict | None:
    """Convierte un tool call en la receta de grafica (o None si no grafica)."""
    pide_grafica = nombre_tool == "generar_grafica" or (
        nombre_tool in ("consultar_inegi", "consultar_banxico") and args.get("graficar")
    )
    if not pide_grafica:
        return None
    fuente = args.get("fuente") or ("INEGI" if nombre_tool == "consultar_inegi" else "Banxico")
    spec = {"fuente": fuente, "serie_id": args["serie_id"], "titulo": args.get("titulo", "")}
    for campo in ("fecha_ini", "fecha_fin", "tipo", "transformacion"):
        if args.get(campo):
            spec[campo] = args[campo]
    return spec


# ---------------------------------------------------------------------------
# Llamada al agente con streaming: se muestran los pasos en vivo (st.status)
# ---------------------------------------------------------------------------
def responder(pregunta: str, historial: list[dict]) -> dict:
    # Contexto corto: ultimas preguntas/respuestas en texto (sin tool calls)
    previos = [
        {"role": m["role"], "content": m["content"]}
        for m in historial[-2 * TURNOS_DE_CONTEXTO:]
    ]
    entrada = {"messages": previos + [{"role": "user", "content": pregunta}]}

    respuesta, graficas, llamadas_llm = "", [], 0
    modelos_usados: list[str] = []  # puede cambiar al respaldo a media respuesta
    pendientes: dict[str, dict] = {}  # tool_call_id -> receta de grafica

    with st.status("Analizando tu pregunta…", expanded=True) as status:
        try:
            # stream_mode="updates": un evento por nodo del grafo (modelo, tools, middleware)
            for evento in obtener_agente().stream(entrada, stream_mode="updates"):
                for nodo, datos in evento.items():
                    if not isinstance(datos, dict):
                        continue
                    for msg in datos.get("messages") or []:
                        if isinstance(msg, AIMessage) and nodo == "model":
                            llamadas_llm += 1
                            nombre = msg.response_metadata.get("model_name")
                            if nombre and nombre not in modelos_usados:
                                modelos_usados.append(nombre)
                            for tc in msg.tool_calls:
                                st.write(NOMBRES_TOOLS.get(tc["name"], f"🔧 {tc['name']}"),
                                         f"`{tc['args'].get('serie_id', '')}`")
                                spec = _spec_grafica(tc["name"], tc["args"])
                                if spec:
                                    pendientes[tc["id"]] = spec
                            if not msg.tool_calls:
                                respuesta = msg.text  # .text une bloques (Gemini devuelve listas)
                        elif isinstance(msg, ToolMessage):
                            if msg.status == "error":
                                st.write(f"⚠️ {msg.name} falló: {str(msg.content)[:150]}")
                            elif msg.tool_call_id in pendientes:
                                # Solo se grafica si la tool termino bien
                                graficas.append(pendientes.pop(msg.tool_call_id))
            status.update(
                label=f"Listo · {llamadas_llm} llamada(s) al LLM · {' → '.join(modelos_usados) or 'modelo'}",
                state="complete",
                expanded=False,
            )
        except Exception as exc:
            status.update(label="Ocurrió un error", state="error")
            texto = str(exc)
            if es_limite_de_cuota(exc):
                respuesta = ("⏳ Se alcanzó el límite del proveedor del LLM (tier gratuito). "
                             "Espera un minuto y vuelve a intentarlo, o cambia LLM_PROVIDER en .env.")
            else:
                respuesta = f"❌ Error al consultar el agente: {texto[:300]}"

    return {"role": "assistant", "content": respuesta or "_(sin respuesta)_", "graficas": graficas}


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Agente")
    proveedor = os.environ.get("LLM_PROVIDER", "groq")
    modelo = os.environ.get(f"{proveedor.upper()}_MODEL", "default")
    st.caption(f"Proveedor LLM: **{proveedor}** · modelo: `{modelo}`")
    if proveedor == "groq":
        respaldo = os.environ.get("GROQ_FALLBACK_MODEL", GROQ_FALLBACK_DEFAULT) or "desactivado"
        st.caption(f"Respaldo si se agota la cuota: `{respaldo}`")
    st.caption(f"Tope de llamadas por pregunta: {os.environ.get('MAX_LLM_CALLS', '5')}")

    st.markdown("### 💡 Preguntas de ejemplo")
    for i, ejemplo in enumerate(PREGUNTAS_EJEMPLO):
        # Al hacer clic se guarda la pregunta y se procesa abajo como si se escribiera
        if st.button(ejemplo, key=f"ej_{i}", width="stretch"):
            st.session_state.pregunta_pendiente = ejemplo

    st.divider()
    if st.button("🗑️ Nueva conversación", width="stretch"):
        st.session_state.historial = []
        st.rerun()
    if st.button("🔄 Actualizar indicadores", width="stretch"):
        cargar_panel.clear()  # borra la cache del panel y vuelve a consultar
        st.rerun()
    st.caption("Fuentes: INEGI (BIE/BISE), Banxico (SIE) y noticias con análisis de sentimiento.")


# ---------------------------------------------------------------------------
# Cuerpo principal: panel + chat
# ---------------------------------------------------------------------------
mostrar_panel()
st.divider()
st.subheader("Conversa con el agente")

# session_state guarda el historial por pestaña del navegador
if "historial" not in st.session_state:
    st.session_state.historial = []

# Re-dibujar la conversacion previa (Streamlit re-ejecuta el script en cada interaccion)
for i, m in enumerate(st.session_state.historial):
    with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "📈"):
        st.markdown(formatear_respuesta(m["content"]))
        for j, spec in enumerate(m.get("graficas", [])):
            mostrar_grafica(spec, key=f"g_{i}_{j}")

# Pregunta nueva: del input de chat o de un boton de ejemplo
pregunta = st.chat_input("Pregunta sobre inflación, tipo de cambio, empleo, tasas…")
pregunta = pregunta or st.session_state.pop("pregunta_pendiente", None)

if pregunta:
    with st.chat_message("user", avatar="🧑"):
        st.markdown(pregunta)
    with st.chat_message("assistant", avatar="📈"):
        mensaje = responder(pregunta, st.session_state.historial)
        st.markdown(formatear_respuesta(mensaje["content"]))
        n = len(st.session_state.historial)
        for j, spec in enumerate(mensaje["graficas"]):
            mostrar_grafica(spec, key=f"g_{n + 1}_{j}")
    st.session_state.historial += [{"role": "user", "content": pregunta}, mensaje]
