"""
generar_grafica — tool LangChain (plan seccion 3).

Estilo fijo tipo ggplot con Plotly; salida HTML (sin PNG/kaleido para evitar cuelgues).
Fechas formateadas estilo es-MX en el eje X.

Recibe fuente + serie_id (no los datos): la serie se lee de la cache compartida
con consultar_inegi/consultar_banxico. Asi el LLM no reescribe miles de puntos
como argumentos y puede pedir datos + grafica en paralelo en un mismo turno.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
from langchain_core.tools import tool

from agent.tools.series_cache import INICIO_DEFAULT, obtener_serie, recortar, transformar

# Salida de figuras (HTML + PNG) dentro del repo
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

# Estilo fijo tipo ggplot2: panel gris claro, rejilla blanca, tipografia fuerte
COLOR_LINEA = "#2C3E50"
COLOR_BARRAS = "#34495E"
COLOR_PANEL = "#EBEBEB"
COLOR_REJILLA = "#FFFFFF"
COLOR_TEXTO = "#222222"
FUENTE_FAMILIA = "Arial, Helvetica, sans-serif"


def _fig(
    fechas: list[str],
    valores: list[float],
    titulo: str,
    fuente: str,
    tipo: str,
    eje_y: str = "Valor",
):
    """Construye la figura Plotly (linea|barras) con look ggplot: panel gris y textos grandes en negrita."""
    fig = go.Figure()
    if tipo == "barras":
        fig.add_trace(
            go.Bar(
                x=fechas,
                y=valores,
                marker_color=COLOR_BARRAS,
                marker_line=dict(width=0),
                name=titulo,
            )
        )
    else:
        # Linea un poco mas gruesa; marcadores suaves para legibilidad
        fig.add_trace(
            go.Scatter(
                x=fechas,
                y=valores,
                mode="lines+markers",
                line=dict(color=COLOR_LINEA, width=3),
                marker=dict(size=6, color=COLOR_LINEA),
                name=titulo,
            )
        )

    # Ejes compartidos: ticks grandes, titulos en negrita, rejilla blanca sobre panel gris
    eje_comun = dict(
        showgrid=True,
        gridcolor=COLOR_REJILLA,
        gridwidth=1.5,
        zeroline=False,
        showline=False,
        tickfont=dict(family=FUENTE_FAMILIA, size=14, color=COLOR_TEXTO),
        title_font=dict(family=FUENTE_FAMILIA, size=18, color=COLOR_TEXTO, weight="bold"),
    )

    fig.update_layout(
        # Fondo exterior blanco; area de trazado gris (ggplot)
        paper_bgcolor="white",
        plot_bgcolor=COLOR_PANEL,
        title=dict(
            text=f"<b>{titulo}</b>",
            font=dict(family=FUENTE_FAMILIA, size=22, color=COLOR_TEXTO),
            x=0.02,
            xanchor="left",
        ),
        font=dict(family=FUENTE_FAMILIA, size=14, color=COLOR_TEXTO),
        xaxis=dict(
            title=dict(text="<b>Fecha</b>"),
            tickformat="%d/%m/%Y",
            **eje_comun,
        ),
        yaxis=dict(title=dict(text=f"<b>{eje_y}</b>"), **eje_comun),
        # Pie de pagina con la fuente del dato
        annotations=[
            dict(
                text=f"<b>Fuente:</b> {fuente}",
                xref="paper",
                yref="paper",
                x=0,
                y=-0.22,
                showarrow=False,
                font=dict(family=FUENTE_FAMILIA, size=12, color="#555555"),
            )
        ],
        margin=dict(l=70, r=30, t=70, b=90),
        height=520,
        width=900,
        showlegend=False,
    )
    return fig


def figura_serie(
    fuente: str,
    serie_id: str,
    titulo: str = "",
    fecha_ini: str = INICIO_DEFAULT,
    fecha_fin: str = "",
    tipo: str = "linea",
    transformacion: str = "nivel",
) -> go.Figure:
    """Figura Plotly con el estilo fijo, leyendo la serie de la cache (la usa tambien la app Streamlit)."""
    if tipo not in ("linea", "barras"):
        raise ValueError("tipo debe ser 'linea' o 'barras'")

    serie = transformar(obtener_serie(fuente, serie_id), transformacion)
    df = recortar(serie, fecha_ini, fecha_fin).dropna(subset=["valor"])
    if df.empty:
        raise ValueError(f"Sin observaciones para {fuente} {serie_id} en el rango pedido")
    fechas = [d.strftime("%Y-%m-%d") for d in df["fecha"]]
    valores = [float(v) for v in df["valor"]]
    eje_y = "Variación anual (%)" if transformacion == "var_anual" else "Valor"
    return _fig(fechas, valores, titulo or f"{fuente} {serie_id}", f"{fuente}, serie {serie_id}", tipo, eje_y)


def graficar_serie(
    fuente: str,
    serie_id: str,
    titulo: str = "",
    fecha_ini: str = INICIO_DEFAULT,
    fecha_fin: str = "",
    tipo: str = "linea",
    transformacion: str = "nivel",
) -> dict:
    """Grafica una serie de la cache y guarda HTML (lo usan generar_grafica y consultar_*)."""
    fig = figura_serie(fuente, serie_id, titulo, fecha_ini, fecha_fin, tipo, transformacion)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = OUT_DIR / f"grafica_{stamp}_{fuente}_{serie_id}.html"
    # Solo HTML: write_image/kaleido puede colgarse minutos si no hay Chrome
    fig.write_html(str(html_path), include_plotlyjs="cdn")

    return {
        "html_path": str(html_path),
        "tipo": tipo,
        "n_puntos": len(fig.data[0].x),
        "fuente": fuente,
    }


@tool
def generar_grafica(
    fuente: str,
    serie_id: str,
    titulo: str,
    fecha_ini: str = INICIO_DEFAULT,
    fecha_fin: str = "",
    tipo: str = "linea",
    transformacion: str = "nivel",
) -> dict:
    """Grafica (linea o barras) de una serie INEGI/Banxico ya identificada, dada su fuente y serie_id; guarda HTML. No requiere pasar los datos. transformacion="var_anual" grafica la variacion % anual."""
    return graficar_serie(fuente, serie_id, titulo, fecha_ini, fecha_fin, tipo, transformacion)
