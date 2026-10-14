"""
Formato de las respuestas del LLM para mostrarlas en Streamlit.

El LLM escribe LaTeX con \\[ ... \\] o \\( ... \\), que el Markdown de Streamlit
no reconoce (se come las barras y quedan "[ \\Delta ... ]"). Streamlit si dibuja
LaTeX (KaTeX) con $$ ... $$ (bloque) y $ ... $ (en linea).
"""

from __future__ import annotations

import re


def _limpiar_latex(formula: str) -> str:
    """Ajustes para KaTeX dentro de una formula."""
    formula = formula.strip()
    formula = re.sub(r"(?<!\\)%", r"\\%", formula)          # % es comentario en LaTeX
    formula = re.sub(r"(?<=\d),(?=\d{3})", "{,}", formula)   # 1,531,900 sin espacios raros
    return formula


def formatear_respuesta(texto: str) -> str:
    """Convierte las formulas del LLM a la sintaxis que Streamlit renderiza."""
    # 1) Pesos tipo "$18.35": escapar el $ para que no se lea como formula
    texto = re.sub(r"(?<![\\$])\$(?=\d)", r"\\$", texto)
    # 2) Bloques \[ ... \] y $$ ... $$ -> $$ ... $$ en su propia linea
    texto = re.sub(
        r"\\\[(.+?)\\\]|\$\$(.+?)\$\$",
        lambda m: f"\n$$\n{_limpiar_latex(m.group(1) or m.group(2))}\n$$\n",
        texto,
        flags=re.S,
    )
    # 2b) Linea completa "[ \comando ... ]" (el \[ ya llego sin barra)
    texto = re.sub(
        r"^[ \t]*\[[ \t]*(\\[A-Za-z].*?)[ \t]*\][ \t]*$",
        lambda m: f"$$\n{_limpiar_latex(m.group(1))}\n$$",
        texto,
        flags=re.M,
    )
    # 3) Formulas en linea \( ... \) -> $ ... $
    texto = re.sub(r"\\\((.+?)\\\)", lambda m: f"${_limpiar_latex(m.group(1))}$", texto, flags=re.S)
    return texto
