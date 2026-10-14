"""
consultar_inegi — tool LangChain (plan seccion 3).

Reutiliza la logica de Descarga_SeriesINEGI.ipynb:
peticion directa a BIE-BISE con requests (sin INEGIpy).
Token solo desde os.environ["INEGI_TOKEN"] (nunca hardcodeado).
"""

from __future__ import annotations

import os

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

# Misma base que en el notebook de descarga
BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"


def _parse_periodo(periodo: str) -> pd.Timestamp:
    """
    TIME_PERIOD de BIE-BISE: "YYYY" (anual), "YYYY/MM" (mensual) o
    "YYYY/MM/QQ" (quincenal: 01 = primera quincena, 02 = segunda).
    """
    partes = str(periodo).strip().split("/")
    try:
        anio = int(partes[0])
        mes = int(partes[1]) if len(partes) > 1 else 1
        dia = 16 if len(partes) > 2 and partes[2] == "02" else 1
        return pd.Timestamp(year=anio, month=mes, day=dia)
    except (ValueError, IndexError):
        return pd.NaT


def _descargar_serie_inegi(serie_id: str) -> pd.DataFrame:
    """
    GET INDICATOR/{id}/es/00/false/BIE-BISE/2.0/{TOKEN}?type=json
    Parsea OBSERVATIONS -> DataFrame (fecha, valor) con la historia completa.
    """
    token = os.environ["INEGI_TOKEN"]
    url = f"{BASE_URL}/INDICATOR/{serie_id}/es/00/false/BIE-BISE/2.0/{token}?type=json"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()
    series = data.get("Series") or []
    if not series:
        raise ValueError(f"INEGI no devolvio Series para id={serie_id}")

    # Observaciones en la primera (y unica) serie del indicador
    obs = series[0].get("OBSERVATIONS") or []
    # TIME_PERIOD / OBS_VALUE: campos estandar de la API BIE-BISE
    df = pd.DataFrame(
        {
            "fecha": [_parse_periodo(o.get("TIME_PERIOD")) for o in obs],
            "valor": pd.to_numeric([o.get("OBS_VALUE") for o in obs], errors="coerce"),
        }
    )
    if df.empty:
        return pd.DataFrame(columns=["fecha", "valor"])
    # La API entrega lo mas reciente primero; ordenar cronologicamente
    return df.dropna(subset=["fecha"]).sort_values("fecha").reset_index(drop=True)


registrar_descargador("INEGI", _descargar_serie_inegi)


@tool
def consultar_inegi(
    serie_id: str,
    fecha_ini: str = INICIO_DEFAULT,
    fecha_fin: str = "",
    n_ultimas: int = N_ULTIMAS_DEFAULT,
    graficar: bool = False,
    titulo: str = "",
) -> dict:
    """Resumen de una serie del INEGI (BIE/BISE) dado su ID: ultimo valor, variaciones, max/min y ultimas n_ultimas observaciones. graficar=True ademas guarda la grafica (titulo opcional)."""
    df = recortar(obtener_serie("INEGI", serie_id), fecha_ini, fecha_fin)
    out = {"fuente": "INEGI", "serie_id": serie_id, **resumir(df, n_ultimas)}
    if graficar and out["n_obs"]:
        # Misma llamada: evita un turno extra del LLM solo para generar_grafica
        out["grafica_html"] = graficar_serie("INEGI", serie_id, titulo, fecha_ini, fecha_fin)["html_path"]
    return out
