"""Ontologia (.ttl) y grafo de OntoRank, sin cargar el modelo de embeddings."""

import numpy as np

from ontology.build_ontology import INDICADORES, _validar_inventario
from ontology.ontorank import _softmax, ttl_a_digraph


def test_inventario_valido():
    _validar_inventario()  # 66 indicadores, 40 INEGI + 26 Banxico, relaciones validas
    assert len(INDICADORES) == 66


def test_grafo_bidireccional_y_metadatos():
    G, meta = ttl_a_digraph()
    # relacionadoCon en ambos sentidos (ver comentario en ttl_a_digraph)
    assert G.has_edge("Tasa_objetivo", "TIIE_28_dias")
    assert G.has_edge("TIIE_28_dias", "Tasa_objetivo")
    inpc = meta["INPC"]
    assert inpc["fuente"] == "INEGI" and inpc["claveAPI"] == "910392"
    assert inpc["unidad"] and inpc["frecuencia"] == "mensual"
    assert "inflacion" in inpc["sinonimos"]


def test_softmax_con_temperatura_concentra_el_peso():
    sims = {"a": 0.85, "b": 0.30, "c": 0.10}
    p = _softmax(sims)
    assert np.isclose(sum(p.values()), 1.0)
    # Con temperatura 0.1 el mas parecido domina (sin ella seria casi uniforme)
    assert p["a"] > 0.99
