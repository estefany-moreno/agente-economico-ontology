"""
Cache en proceso de series INEGI/Banxico + resumen compacto para el LLM.

Objetivo: reducir tokens y llamadas al modelo.
- Cada serie se descarga una sola vez y se refresca tras SERIES_TTL_HORAS
  (consultar_*, generar_grafica y la app Streamlit comparten el mismo DataFrame).
- Al LLM solo le llega un resumen ya calculado (ultimo valor, variaciones,
  min/max, ultimas observaciones), nunca la serie completa: una serie diaria
  de Banxico desde 1993 son ~8,500 observaciones (~60k tokens).
"""

from __future__ import annotations

import os
import time
from datetime import date
from typing import Callable

import pandas as pd

# (fuente, serie_id) -> (momento de descarga, DataFrame completo [fecha, valor])
_CACHE: dict[tuple[str, str], tuple[float, pd.DataFrame]] = {}
# Vigencia de una serie en cache: en procesos largos (app Streamlit) evita
# servir datos viejos, p. ej. el tipo de cambio diario
TTL_SEGUNDOS = float(os.environ.get("SERIES_TTL_HORAS", "6")) * 3600
# fuente -> funcion de descarga de historia completa (registrada por cada tool)
_DESCARGADORES: dict[str, Callable[[str], pd.DataFrame]] = {}

# Inicio comun de las series (mismo default que los notebooks)
INICIO_DEFAULT = "1993-01-01"
N_ULTIMAS_DEFAULT = 12
N_ULTIMAS_MAX = 60


def registrar_descargador(fuente: str, fn: Callable[[str], pd.DataFrame]) -> None:
    """Cada tool de datos registra como bajar la historia completa de una serie."""
    _DESCARGADORES[fuente] = fn


def obtener_serie(fuente: str, serie_id: str) -> pd.DataFrame:
    """Historia completa de la serie; se descarga una vez y se reusa durante TTL_SEGUNDOS."""
    clave = (fuente, str(serie_id).strip())
    guardada = _CACHE.get(clave)
    if guardada is None or time.time() - guardada[0] > TTL_SEGUNDOS:
        if fuente not in _DESCARGADORES:
            raise ValueError(f"fuente desconocida: {fuente!r}. Use INEGI | Banxico.")
        guardada = (time.time(), _DESCARGADORES[fuente](clave[1]))
        _CACHE[clave] = guardada
    return guardada[1]


def recortar(df: pd.DataFrame, fecha_ini: str, fecha_fin: str) -> pd.DataFrame:
    """Recorta a [fecha_ini, fecha_fin]; fecha_fin vacia = hoy."""
    if df.empty:
        return df
    ini = pd.Timestamp(fecha_ini)
    fin = pd.Timestamp(fecha_fin or date.today().isoformat())
    return df.loc[(df["fecha"] >= ini) & (df["fecha"] <= fin)].reset_index(drop=True)


def _num(v) -> float | None:
    return None if pd.isna(v) else round(float(v), 4)


def _pct(actual, previo) -> float | None:
    if pd.isna(actual) or pd.isna(previo) or previo == 0:
        return None
    return round((float(actual) / float(previo) - 1) * 100, 2)


def resumir(df: pd.DataFrame, n_ultimas: int = N_ULTIMAS_DEFAULT) -> dict:
    """Estadisticos precalculados para que el LLM no reciba ni recalcule la serie."""
    df = df.dropna(subset=["valor"])
    if df.empty:
        return {"n_obs": 0}

    ult = df.iloc[-1]
    resumen = {
        "n_obs": int(len(df)),
        "primera_fecha": df["fecha"].iloc[0].strftime("%Y-%m-%d"),
        "ultima_fecha": ult["fecha"].strftime("%Y-%m-%d"),
        "ultimo_valor": _num(ult["valor"]),
    }

    # Variacion vs observacion previa (mensual, diaria, etc. segun frecuencia)
    if len(df) > 1:
        prev = df.iloc[-2]
        resumen["valor_previo"] = _num(prev["valor"])
        resumen["var_pct_vs_previo"] = _pct(ult["valor"], prev["valor"])

    # Variacion anual: ultima observacion con fecha <= un año antes
    hace_un_anio = df.loc[df["fecha"] <= ult["fecha"] - pd.DateOffset(years=1)]
    if not hace_un_anio.empty:
        base = hace_un_anio.iloc[-1]
        resumen["valor_hace_un_anio"] = _num(base["valor"])
        resumen["fecha_hace_un_anio"] = base["fecha"].strftime("%Y-%m-%d")
        resumen["var_pct_anual"] = _pct(ult["valor"], base["valor"])

    imax, imin = df["valor"].idxmax(), df["valor"].idxmin()
    resumen["maximo"] = {"fecha": df.at[imax, "fecha"].strftime("%Y-%m-%d"), "valor": _num(df.at[imax, "valor"])}
    resumen["minimo"] = {"fecha": df.at[imin, "fecha"].strftime("%Y-%m-%d"), "valor": _num(df.at[imin, "valor"])}
    resumen["promedio_periodo"] = _num(df["valor"].mean())

    n = max(1, min(int(n_ultimas), N_ULTIMAS_MAX))
    cola = df.tail(n)
    resumen["ultimas_observaciones"] = [
        [d.strftime("%Y-%m-%d"), _num(v)] for d, v in zip(cola["fecha"], cola["valor"])
    ]
    return resumen
