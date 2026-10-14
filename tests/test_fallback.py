"""Cambio automatico al modelo de respaldo ante limite de cuota (429)."""

import pytest

from agent import fallback
from agent.fallback import FallbackPorCuotaMiddleware, es_limite_de_cuota, segundos_de_espera


class Error429(Exception):
    status_code = 429


class RateLimitError(Exception):
    """Mismo nombre que la excepcion de los SDKs de Groq/OpenAI."""


class RequestFalsa:
    def __init__(self, model="principal"):
        self.model = model

    def override(self, model):
        return RequestFalsa(model)


def test_es_limite_de_cuota():
    assert es_limite_de_cuota(Error429())
    assert es_limite_de_cuota(RateLimitError())
    assert not es_limite_de_cuota(ValueError("heartbeatRate quota"))  # el texto no cuenta


@pytest.mark.parametrize(
    "mensaje, segundos",
    [
        ("Please try again in 21m24.336s.", 1284.336),
        ("try again in 2.5s", 2.5),
        ("try again in 1h2m3s", 3723.0),
        ("sin indicacion", fallback.ESPERA_DEFAULT_S),
    ],
)
def test_segundos_de_espera(mensaje, segundos):
    assert segundos_de_espera(Exception(mensaje)) == pytest.approx(segundos)


def test_cambia_al_respaldo_y_recuerda_el_bloqueo():
    mw = FallbackPorCuotaMiddleware(respaldo="respaldo")
    usados = []

    def handler(request):
        usados.append(request.model)
        if request.model == "principal":
            raise Error429("try again in 30s")
        return f"ok:{request.model}"

    # 1a llamada: el principal falla con 429 -> responde el respaldo
    assert mw.wrap_model_call(RequestFalsa(), handler) == "ok:respaldo"
    # 2a llamada: va directo al respaldo, sin gastar una request en el principal
    assert mw.wrap_model_call(RequestFalsa(), handler) == "ok:respaldo"
    assert usados == ["principal", "respaldo", "respaldo"]


def test_vuelve_al_principal_al_terminar_el_bloqueo(monkeypatch):
    mw = FallbackPorCuotaMiddleware(respaldo="respaldo")
    reloj = {"t": 1000.0}
    monkeypatch.setattr(fallback.time, "time", lambda: reloj["t"])
    estado = {"sin_cuota": True}

    def handler(request):
        if request.model == "principal" and estado["sin_cuota"]:
            raise Error429("try again in 10s")
        return request.model

    assert mw.wrap_model_call(RequestFalsa(), handler) == "respaldo"
    reloj["t"] += 11
    estado["sin_cuota"] = False
    assert mw.wrap_model_call(RequestFalsa(), handler) == "principal"


def test_otros_errores_no_se_ocultan():
    mw = FallbackPorCuotaMiddleware(respaldo="respaldo")

    def handler(request):
        raise ValueError("bug real")

    with pytest.raises(ValueError):
        mw.wrap_model_call(RequestFalsa(), handler)
