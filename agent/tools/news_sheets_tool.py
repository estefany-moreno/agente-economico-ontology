"""
consultar_noticias — tool LangChain (plan seccion 3).

Lectura sola de Google Sheets (hoja noticias_con_sentimiento) via gspread
+ cuenta de servicio (GOOGLE_APPLICATION_CREDENTIALS, SHEET_KEY).

El agregado de sentimiento se calcula en Python (no lo estima el LLM):
promedio de sentiment_score y conteos por sentimiento (-1, 0, 1).
"""

from __future__ import annotations

import os
import re
from datetime import date, timedelta

import gspread
import pandas as pd
from langchain_core.tools import tool

from agent.tools.errores import ErrorDeFuente

# Hoja acordada para el agente
HOJA = "noticias_con_sentimiento"
# Columnas que el agente puede citar (orden de la hoja documentado por la usuaria)
COLS = ["sentimiento", "sentiment_score", "texto_input_80tokens", "fecha", "url"]


def _id_hoja(valor: str) -> str:
    """
    Acepta en SHEET_KEY el ID o la URL completa del Google Sheet y devuelve el ID.
    Ej.: ".../spreadsheets/d/<ID>/edit?gid=0" o "<ID>/edit?gid=0" -> "<ID>".
    """
    valor = valor.strip()
    m = re.search(r"/d/([A-Za-z0-9_-]+)", valor)
    if m:
        return m.group(1)
    return re.split(r"[/?#]", valor, maxsplit=1)[0]


def _leer_hoja() -> pd.DataFrame:
    """Abre el spreadsheet con cuenta de servicio y carga la hoja de sentimiento."""
    try:
        # gspread usa el JSON apuntado por GOOGLE_APPLICATION_CREDENTIALS
        gc = gspread.service_account(filename=os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        sh = gc.open_by_key(_id_hoja(os.environ["SHEET_KEY"]))
        rows = sh.worksheet(HOJA).get_all_records()
    except gspread.exceptions.WorksheetNotFound:
        raise ErrorDeFuente(f"El Google Sheet no tiene la pestaña '{HOJA}'.") from None
    except gspread.exceptions.SpreadsheetNotFound:
        raise ErrorDeFuente(
            "No se encontro el Google Sheet de noticias: revisa SHEET_KEY y que la "
            "hoja este compartida con la cuenta de servicio."
        ) from None
    except (PermissionError, gspread.exceptions.APIError) as exc:
        # gspread convierte el 403 en PermissionError; otros codigos llegan como APIError
        codigo = getattr(getattr(exc, "response", None), "status_code", 403)
        if codigo == 429:
            raise ErrorDeFuente("Se excedio la cuota de lectura de Google Sheets; intenta en un minuto.") from None
        if codigo == 404:
            raise ErrorDeFuente("No se encontro el Google Sheet de noticias: revisa SHEET_KEY.") from None
        raise ErrorDeFuente(
            "Sin acceso al Google Sheet de noticias: verifica que la Google Sheets API este "
            "habilitada en el proyecto de la cuenta de servicio y que la hoja este compartida "
            "con su correo (client_email de credentials.json)."
        ) from None
    return pd.DataFrame(rows)


@tool
def consultar_noticias(
    fecha_ini: str = "",
    fecha_fin: str = "",
    dias_atras: int = 7,
    n_maximo: int = 15,
    palabra_clave: str | None = None,
) -> dict:
    """Noticias (texto corto + sentimiento) y resumen agregado del tono. Para un periodo concreto (p. ej. "abril 2026") usa fecha_ini y fecha_fin (YYYY-MM-DD); sin fechas, toma los ultimos dias_atras dias. Usa palabra_clave solo si el usuario pide un tema concreto (p. ej. "aranceles"); para el tono general dejala vacia."""
    df = _leer_hoja()
    # Asegurar columnas esperadas aunque el sheet traiga extras
    for c in COLS:
        if c not in df.columns:
            raise ErrorDeFuente(f"Falta la columna '{c}' en la pestaña {HOJA}")

    df = df[COLS].copy()
    # format="mixed": tolera filas con y sin hora (si no, pandas toma el formato
    # de la primera fila y convierte en NaT, en silencio, las que no coinciden)
    df["fecha"] = pd.to_datetime(df["fecha"].astype(str), errors="coerce", format="mixed")
    df["sentimiento"] = pd.to_numeric(df["sentimiento"], errors="coerce")
    df["sentiment_score"] = pd.to_numeric(df["sentiment_score"], errors="coerce")
    # Rango que cubre la hoja: se reporta si el periodo pedido queda vacio
    disponibles = {
        "desde": df["fecha"].min().strftime("%Y-%m-%d") if df["fecha"].notna().any() else None,
        "hasta": df["fecha"].max().strftime("%Y-%m-%d") if df["fecha"].notna().any() else None,
    }

    # Ventana temporal: periodo explicito [fecha_ini, fecha_fin] o ultimos dias_atras
    if fecha_ini or fecha_fin:
        desde = pd.Timestamp(fecha_ini) if fecha_ini else df["fecha"].min()
        hasta = pd.Timestamp(fecha_fin) if fecha_fin else pd.Timestamp(date.today())
    else:
        desde = pd.Timestamp(date.today() - timedelta(days=int(dias_atras)))
        hasta = pd.Timestamp(date.today())
    # fecha_fin inclusiva: todo el dia (las fechas de la hoja pueden traer hora)
    df = df.loc[(df["fecha"] >= desde) & (df["fecha"] < hasta + pd.Timedelta(days=1))]

    # Filtro opcional solo sobre texto_input_80tokens (case-insensitive)
    if palabra_clave:
        mask = (
            df["texto_input_80tokens"]
            .astype(str)
            .str.contains(palabra_clave, case=False, na=False)
        )
        df = df.loc[mask]

    # Agregados confiables en Python sobre TODAS las noticias del periodo
    # (sentimiento: 1 / -1 / 0), no solo sobre las que se listan abajo
    scores = df["sentiment_score"].dropna()
    sent = df["sentimiento"]
    resumen = {
        "periodo": {
            "desde": None if pd.isna(desde) else desde.strftime("%Y-%m-%d"),
            "hasta": hasta.strftime("%Y-%m-%d"),
        },
        "sentimiento_promedio": round(float(scores.mean()), 4) if len(scores) else None,
        "n_positivas": int((sent == 1).sum()),
        "n_negativas": int((sent == -1).sum()),
        "n_neutrales": int((sent == 0).sum()),
        "n_total": int(len(df)),
        "palabra_clave": palabra_clave,
    }

    # Mas recientes primero; solo n_maximo filas individuales para el LLM (tokens)
    df = df.sort_values("fecha", ascending=False).head(int(n_maximo))
    resumen["n_mostradas"] = int(len(df))
    if resumen["n_total"] == 0:
        # Evita que el agente reintente a ciegas: le dice que fechas si hay
        resumen["noticias_disponibles"] = disponibles

    noticias = []
    for _, row in df.iterrows():
        noticias.append(
            {
                "fecha": None
                if pd.isna(row["fecha"])
                else row["fecha"].strftime("%Y-%m-%d"),
                "texto_input_80tokens": row["texto_input_80tokens"],
                "sentimiento": None
                if pd.isna(row["sentimiento"])
                else int(row["sentimiento"]),
                "sentiment_score": None
                if pd.isna(row["sentiment_score"])
                else float(row["sentiment_score"]),
                "url": row["url"],
            }
        )

    return {"resumen": resumen, "noticias": noticias}
