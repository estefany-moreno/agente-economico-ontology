"""Tool de noticias: ID de la hoja, filtro por periodo y resumen de sentimiento."""

import pandas as pd
import pytest

from agent.tools import news_sheets_tool
from agent.tools.news_sheets_tool import _id_hoja, consultar_noticias


@pytest.mark.parametrize(
    "valor",
    [
        "ABC_def-123",
        " ABC_def-123 ",
        "ABC_def-123/edit?pli=1&gid=5#gid=5",
        "https://docs.google.com/spreadsheets/d/ABC_def-123/edit?gid=0#gid=0",
    ],
)
def test_id_hoja_acepta_id_o_url(valor):
    assert _id_hoja(valor) == "ABC_def-123"


@pytest.fixture
def hoja_falsa(monkeypatch):
    """20 noticias en abril 2026 (10 positivas, 10 negativas) y 2 en mayo."""
    filas = []
    for i in range(20):
        positiva = i % 2 == 0
        filas.append({
            "sentimiento": 1 if positiva else -1,
            "sentiment_score": 0.5 if positiva else -0.5,
            "texto_input_80tokens": f"nota {i} sobre aranceles" if i < 4 else f"nota {i}",
            "fecha": f"2026-04-{i + 1:02d} 10:00:00",
            "url": f"https://ejemplo.mx/{i}",
        })
    for d in (5, 6):
        filas.append({"sentimiento": 0, "sentiment_score": 0.0, "texto_input_80tokens": "mayo",
                      "fecha": f"2026-05-{d:02d}", "url": "https://ejemplo.mx/m"})
    monkeypatch.setattr(news_sheets_tool, "_leer_hoja", lambda: pd.DataFrame(filas))


def test_periodo_explicito_y_resumen_sobre_todo_el_periodo(hoja_falsa):
    r = consultar_noticias.invoke({"fecha_ini": "2026-04-01", "fecha_fin": "2026-04-30", "n_maximo": 5})
    res = r["resumen"]
    # El resumen cubre las 20 de abril, aunque solo se listan 5
    assert res["n_total"] == 20
    assert res["n_mostradas"] == 5 and len(r["noticias"]) == 5
    assert (res["n_positivas"], res["n_negativas"]) == (10, 10)
    assert res["sentimiento_promedio"] == 0.0
    # Mas recientes primero
    assert r["noticias"][0]["fecha"] == "2026-04-20"


def test_fecha_fin_es_inclusiva_con_hora(hoja_falsa):
    r = consultar_noticias.invoke({"fecha_ini": "2026-04-20", "fecha_fin": "2026-04-20"})
    assert r["resumen"]["n_total"] == 1  # la nota de las 10:00 del dia 20 entra


def test_palabra_clave(hoja_falsa):
    r = consultar_noticias.invoke({"fecha_ini": "2026-04-01", "fecha_fin": "2026-04-30", "palabra_clave": "ARANCELES"})
    assert r["resumen"]["n_total"] == 4


def test_periodo_vacio_informa_rango_disponible(hoja_falsa):
    r = consultar_noticias.invoke({"fecha_ini": "2026-09-01", "fecha_fin": "2026-09-30"})
    assert r["resumen"]["n_total"] == 0
    assert r["resumen"]["noticias_disponibles"] == {"desde": "2026-04-01", "hasta": "2026-05-06"}
