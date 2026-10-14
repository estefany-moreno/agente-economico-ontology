"""
consultar_banxico — tool LangChain (plan seccion 3).

Reutiliza Descarga_SeriesBANXICO.ipynb:
GET /series/{id}/datos/{fechaIni}/{fechaFin} con header Bmx-Token.
Token solo desde os.environ["BANXICO_TOKEN"].
"""

from __future__ import annotations

import os
from datetime import date

import pandas as pd
import requests
from langchain_core.tools import tool

from agent.tools.chart_tool import graficar_serie
from agent.tools.series_cache import (
    INICIO_DEFAULT,
    N_ULTIMAS_DEFAULT,
    obtener_serie,
    recortar,
    registrar_descargador,
    resumir,
)

BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1"


def _descargar_serie_banxico(serie_id: str) -> pd.DataFrame:
    """Descarga observaciones SIE desde INICIO_DEFAULT; fechas API en yyyy-MM-dd; respuesta dd/mm/yyyy."""
    token = os.environ["BANXICO_TOKEN"]
    headers = {"Bmx-Token": token}
    url = f"{BASE_URL}/series/{serie_id}/datos/{INICIO_DEFAULT}/{date.today().isoformat()}"
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Error Banxico {r.status_code}: {r.text[:200]}")

    series = r.json().get("bmx", {}).get("series", [])
    if not series or not series[0].get("datos"):
        return pd.DataFrame(columns=["fecha", "valor"])

    # Misma limpieza que el notebook: comas de miles y "N/E"
    df = pd.DataFrame(series[0]["datos"])
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y")
    df["valor"] = pd.to_numeric(
        df["dato"].astype(str).str.replace(",", "", regex=False).replace("N/E", pd.NA),
        errors="coerce",
    )
    return df[["fecha", "valor"]].sort_values("fecha").reset_index(drop=True)


registrar_descargador("Banxico", _descargar_serie_banxico)


@tool
def consultar_banxico(
    serie_id: str,
    fecha_ini: str = INICIO_DEFAULT,
    fecha_fin: str = "",
    n_ultimas: int = N_ULTIMAS_DEFAULT,
    graficar: bool = False,
    titulo: str = "",
) -> dict:
    """Resumen de una serie del SIE de Banxico dado su ID: ultimo valor, variaciones, max/min y ultimas n_ultimas observaciones. graficar=True ademas guarda la grafica (titulo opcional)."""
    df = recortar(obtener_serie("Banxico", serie_id), fecha_ini, fecha_fin)
    out = {"fuente": "Banxico", "serie_id": serie_id, **resumir(df, n_ultimas)}
    if graficar and out["n_obs"]:
        # Misma llamada: evita un turno extra del LLM solo para generar_grafica
        out["grafica_html"] = graficar_serie("Banxico", serie_id, titulo, fecha_ini, fecha_fin)["html_path"]
    return out
