"""Descarga/parseo de series y resumen compacto que recibe el LLM."""

import pandas as pd
import pytest

from agent.tools import inegi_tool, series_cache
from agent.tools.inegi_tool import _descargar_serie_inegi, _parse_periodo
from agent.tools.series_cache import obtener_serie, recortar, registrar_descargador, resumir


# --- Fechas de INEGI (BIE-BISE) -------------------------------------------
@pytest.mark.parametrize(
    "periodo, esperado",
    [
        ("2026/07", "2026-07-01"),      # mensual
        ("2025", "2025-01-01"),         # anual
        ("2024/07/01", "2024-07-01"),   # quincenal: primera quincena
        ("2024/07/02", "2024-07-16"),   # quincenal: segunda quincena
    ],
)
def test_parse_periodo(periodo, esperado):
    assert _parse_periodo(periodo) == pd.Timestamp(esperado)


def test_parse_periodo_invalido_es_nat():
    assert pd.isna(_parse_periodo("sin fecha"))


def test_descarga_inegi_ordena_y_convierte(monkeypatch):
    """La API entrega lo mas reciente primero y valores como texto."""
    monkeypatch.setenv("INEGI_TOKEN", "token-de-prueba")

    class RespuestaFalsa:
        def raise_for_status(self):
            pass

        def json(self):
            return {"Series": [{"OBSERVATIONS": [
                {"TIME_PERIOD": "2026/02", "OBS_VALUE": "102.5"},
                {"TIME_PERIOD": "2026/01", "OBS_VALUE": "101.0"},
                {"TIME_PERIOD": "2025/12", "OBS_VALUE": None},
            ]}]}

    monkeypatch.setattr(inegi_tool.requests, "get", lambda *a, **k: RespuestaFalsa())
    df = _descargar_serie_inegi("123")
    assert list(df["fecha"]) == [pd.Timestamp("2025-12-01"), pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")]
    assert df["valor"].iloc[-1] == 102.5
    assert pd.isna(df["valor"].iloc[0])


# --- Resumen para el LLM ------------------------------------------------------
@pytest.fixture
def serie_mensual():
    """25 meses: 100, 101, ..., 124."""
    fechas = pd.date_range("2024-01-01", periods=25, freq="MS")
    return pd.DataFrame({"fecha": fechas, "valor": [100.0 + i for i in range(25)]})


def test_resumir_variaciones(serie_mensual):
    r = resumir(serie_mensual, n_ultimas=3)
    assert r["n_obs"] == 25
    assert r["ultima_fecha"] == "2026-01-01"
    assert r["ultimo_valor"] == 124.0
    assert r["valor_previo"] == 123.0
    assert r["var_pct_vs_previo"] == round((124 / 123 - 1) * 100, 2)
    assert r["fecha_hace_un_anio"] == "2025-01-01"
    assert r["var_pct_anual"] == round((124 / 112 - 1) * 100, 2)
    assert r["maximo"] == {"fecha": "2026-01-01", "valor": 124.0}
    assert r["minimo"] == {"fecha": "2024-01-01", "valor": 100.0}
    assert r["ultimas_observaciones"] == [["2025-11-01", 122.0], ["2025-12-01", 123.0], ["2026-01-01", 124.0]]


def test_resumir_limita_observaciones(serie_mensual):
    assert len(resumir(serie_mensual, n_ultimas=1000)["ultimas_observaciones"]) == 25
    assert len(resumir(serie_mensual, n_ultimas=0)["ultimas_observaciones"]) == 1


def test_resumir_vacia():
    assert resumir(pd.DataFrame(columns=["fecha", "valor"])) == {"n_obs": 0}


def test_recortar(serie_mensual):
    df = recortar(serie_mensual, "2025-01-01", "2025-03-01")
    assert list(df["valor"]) == [112.0, 113.0, 114.0]


# --- Cache en proceso ---------------------------------------------------------
def test_cache_descarga_una_vez_y_respeta_ttl(monkeypatch, serie_mensual):
    llamadas = []

    def descargar(serie_id):
        llamadas.append(serie_id)
        return serie_mensual

    registrar_descargador("Prueba", descargar)
    series_cache._CACHE.pop(("Prueba", "X"), None)

    obtener_serie("Prueba", "X")
    obtener_serie("Prueba", " X ")  # mismo id con espacios
    assert llamadas == ["X"]

    # Vencido el TTL se vuelve a descargar
    monkeypatch.setattr(series_cache, "TTL_SEGUNDOS", -1)
    obtener_serie("Prueba", "X")
    assert llamadas == ["X", "X"]


def test_fuente_desconocida():
    with pytest.raises(ValueError):
        obtener_serie("FuenteInexistente", "1")


# --- Transformaciones ---------------------------------------------------------
def test_var_anual_mensual(serie_mensual):
    from agent.tools.series_cache import transformar

    df = transformar(serie_mensual, "var_anual")
    # Los primeros 12 meses no tienen base de un año antes
    assert len(df) == 13
    assert df["fecha"].iloc[0] == pd.Timestamp("2025-01-01")
    assert df["valor"].iloc[-1] == pytest.approx((124 / 112 - 1) * 100)


def test_var_anual_diaria_tolera_dias_inhabiles():
    from agent.tools.series_cache import transformar

    # Serie de dias habiles: el 2025-01-04 (sabado) no existe; se usa el viernes 3
    fechas = pd.bdate_range("2024-01-01", "2025-01-06")
    df = pd.DataFrame({"fecha": fechas, "valor": [100.0] * (len(fechas) - 1) + [110.0]})
    r = transformar(df, "var_anual")
    assert r["valor"].iloc[-1] == pytest.approx(10.0)


def test_transformacion_invalida(serie_mensual):
    from agent.tools.series_cache import transformar

    with pytest.raises(ValueError):
        transformar(serie_mensual, "logaritmo")


def test_resumir_en_puntos_porcentuales():
    df = pd.DataFrame({"fecha": pd.date_range("2025-01-01", periods=13, freq="MS"),
                       "valor": [4.0] * 12 + [3.5]})
    r = resumir(df, en_pp=True)
    assert r["cambio_pp_vs_previo"] == -0.5
    assert r["cambio_pp_anual"] == -0.5
    assert "var_pct_anual" not in r
