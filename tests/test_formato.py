"""Conversion de formulas LaTeX del LLM a la sintaxis de Streamlit."""

from agent.formato import formatear_respuesta


def test_bloque_con_barras():
    salida = formatear_respuesta(r"\[ \Delta = 1,531,900.1 - 1,501,411.3 \]")
    assert "$$\n\\Delta = 1{,}531{,}900.1 - 1{,}501{,}411.3\n$$" in salida


def test_bloque_sin_barra_inicial():
    salida = formatear_respuesta(r"[ \text{Variación %} = \frac{a}{b} ]")
    assert salida.startswith("$$\n\\text{Variación \\%}")


def test_en_linea_y_porcentaje():
    assert formatear_respuesta(r"la tasa \(r = 6.5%\).") == r"la tasa $r = 6.5\%$."


def test_pesos_no_se_vuelven_formula():
    assert formatear_respuesta("paso de $18.25 a $18.35") == r"paso de \$18.25 a \$18.35"


def test_corchetes_normales_intactos():
    texto = "[ver nota] y [1, 2, 3]"
    assert formatear_respuesta(texto) == texto
