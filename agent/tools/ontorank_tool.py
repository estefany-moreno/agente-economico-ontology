"""
buscar_indicador_relevante — tool LangChain (arquitectura / seccion 4).

Envuelve OntoRank: aterriza la pregunta del usuario en nodos de la ontologia
antes de consultar INEGI/Banxico. No es un paso fijo del pipeline; el agente
la llama como tool.
"""

from __future__ import annotations

from langchain_core.tools import tool

# Import perezoso del ranker para no cargar sentence-transformers al importar el paquete
_ranker = None


def _get_ranker():
    """Singleton: carga grafo + embeddings una sola vez por proceso."""
    global _ranker
    if _ranker is None:
        from ontology.ontorank import OntoRank

        _ranker = OntoRank()
    return _ranker


def contexto_ontorank(pregunta: str, k: int = 8) -> str:
    """
    Top-k de OntoRank como texto compacto (una linea por nodo) para inyectarlo
    en la pregunta antes de la primera llamada al LLM. Corre local (sin API),
    asi el agente no gasta un turno de modelo solo en llamar a la tool.
    k=8 (no 5) para cubrir preguntas que comparan dos indicadores; cuesta
    ~120 tokens mas, mucho menos que una llamada extra al LLM.
    """
    lineas = [
        f"- {r['id']} | {r['label']} | fuente={r['fuente']} | claveAPI={r['claveAPI'] or '-'}"
        f" | unidad={r['unidad'] or '-'} | frecuencia={r['frecuencia'] or '-'}"
        for r in _get_ranker().rank(pregunta, k=int(k))
    ]
    return "[OntoRank: indicadores mas relevantes]\n" + "\n".join(lineas)


@tool
def buscar_indicador_relevante(pregunta: str, k: int = 5) -> dict:
    """Rankea indicadores/conceptos de la ontologia relevantes a la pregunta (OntoRank)."""
    top = _get_ranker().rank(pregunta, k=int(k))
    return {"pregunta": pregunta, "top": top}
