"""
ontorank.py
-----------
OntoRank = PageRank personalizado (topic-sensitive) sobre la ontologia economica
(plan_de_trabajo.md, seccion 2).

Pipeline:
1. Cargar indicadores.ttl con rdflib y convertirlo a networkx.DiGraph
   (nodos = Indicador / ConceptoNoticias; aristas = relacionadoCon y perteneceABloque).
2. Pre-calcular embeddings locales de la etiqueta de cada nodo
   (sentence-transformers: paraphrase-multilingual-MiniLM-L12-v2).
3. Ante una pregunta: embeberla, similitud coseno vs nodos -> personalizacion ->
   networkx.pagerank(..., alpha=0.85).
4. Devolver top-k con fuente y claveAPI para que el agente elija la tool de datos.

Uso:
    from ontology.ontorank import OntoRank
    ranker = OntoRank()                 # carga grafo + embeddings (cache en disco)
    print(ranker.rank("como va la inflacion?", k=5))
"""

from __future__ import annotations

# Cache de embeddings en disco para no re-encodear en cada arranque
import json
from pathlib import Path

# numpy: vectores, coseno y softmax de personalizacion
import numpy as np

# networkx: DiGraph + pagerank personalizado
import networkx as nx

# rdflib: lectura del Turtle
from rdflib import Graph, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import SKOS

# sentence-transformers: embeddings multilingüe locales (sin API key)
from sentence_transformers import SentenceTransformer


# Rutas y constantes alineadas con build_ontology.py
ONTOLOGY_DIR = Path(__file__).resolve().parent
TTL_PATH = ONTOLOGY_DIR / "indicadores.ttl"
# Cache de embeddings: se regenera si cambia el .ttl o el modelo
EMB_CACHE = ONTOLOGY_DIR / ".ontorank_embeddings.npz"
META_CACHE = ONTOLOGY_DIR / ".ontorank_embeddings_meta.json"

AE = Namespace("http://agente-economico.local/ontologia#")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
# Tipos de nodo que participan en OntoRank (indicadores + concepto noticias)
NODE_TYPES = (AE.Indicador, AE.ConceptoNoticias)
# Temperatura del softmax: los cosenos viven en [0, 1], asi que sin escalar la
# personalizacion queda casi uniforme y PageRank premia solo la estructura del
# grafo (p. ej. M4 salia top para "tipo de cambio"). 0.1 concentra el peso en
# los nodos semanticamente cercanos sin anular la propagacion por aristas.
TEMPERATURA = 0.1


def _local(uri: URIRef) -> str:
    """Extrae el nombre local de una URI (despues de #)."""
    return str(uri).rsplit("#", 1)[-1]


def _softmax(scores: dict[str, float], temperatura: float = TEMPERATURA) -> dict[str, float]:
    """Convierte similitudes en distribucion de probabilidad (personalizacion)."""
    keys = list(scores)
    x = np.array([scores[k] for k in keys], dtype=float) / temperatura
    x = x - x.max()  # estabilidad numerica
    e = np.exp(x)
    e = e / e.sum()
    return {k: float(v) for k, v in zip(keys, e)}


def ttl_a_digraph(ttl_path: Path = TTL_PATH) -> tuple[nx.DiGraph, dict[str, dict]]:
    """
    Paso 1 del plan: RDF -> DiGraph.
    Nodos: Indicador y ConceptoNoticias.
    Aristas (en ambos sentidos): relacionadoCon (entre nodos) y perteneceABloque
    (indicador <-> bloque).
    Los bloques se agregan como nodos intermedios para propagar ranking por tema.
    """
    g_rdf = Graph()
    g_rdf.parse(ttl_path, format="turtle")

    G = nx.DiGraph()
    meta: dict[str, dict] = {}

    # Registrar nodos rankeables (indicadores + noticias) con metadatos para el agente
    for tipo in NODE_TYPES:
        for s in g_rdf.subjects(RDF.type, tipo):
            nid = _local(s)
            label = g_rdf.value(s, RDFS.label)
            fuente = g_rdf.value(s, AE.fuente)
            clave = g_rdf.value(s, AE.claveAPI)
            unidad = g_rdf.value(s, AE.unidad)
            frecuencia = g_rdf.value(s, AE.frecuencia)
            G.add_node(nid)
            meta[nid] = {
                "label": str(label) if label is not None else nid,
                "fuente": _local(fuente) if isinstance(fuente, URIRef) else "",
                "claveAPI": str(clave) if clave is not None else "",
                "unidad": str(unidad) if unidad is not None else "",
                "frecuencia": str(frecuencia) if frecuencia is not None else "",
                # skos:altLabel: sinonimos coloquiales ("inflacion" -> INPC)
                "sinonimos": sorted(str(a) for a in g_rdf.objects(s, SKOS.altLabel)),
                "tipo": _local(tipo),
            }

    # Aristas relacionadoCon (solo si ambos extremos existen en G)
    for s, _, o in g_rdf.triples((None, AE.relacionadoCon, None)):
        a, b = _local(s), _local(o)
        if a not in G:
            G.add_node(a)
        if b not in G:
            G.add_node(b)
        # Arista en ambos sentidos: la relacion economica es simetrica. Si solo
        # fuera a -> b, PageRank le pasaria todo el peso de a a sus vecinos
        # (p. ej. Tasa_objetivo -> CETES dejaba a la tasa fuera del top)
        G.add_edge(a, b)
        G.add_edge(b, a)

    # Aristas perteneceABloque: indicador <-> bloque (el bloque entra al grafo)
    for s, _, o in g_rdf.triples((None, AE.perteneceABloque, None)):
        a, b = _local(s), _local(o)
        if a not in G:
            continue
        if b not in meta:
            # Bloque solo como nodo estructural; sin claveAPI de serie
            blabel = g_rdf.value(o, RDFS.label)
            meta[b] = {
                "label": str(blabel) if blabel is not None else b,
                "fuente": "",
                "claveAPI": "",
                "unidad": "",
                "frecuencia": "",
                "sinonimos": [],
                "tipo": "Bloque",
            }
        G.add_node(b)
        # Bidireccional: el bloque reparte peso a sus indicadores hermanos
        # (pregunta de "empleo" -> todos los del BloqueEmpleo suben un poco)
        G.add_edge(a, b)
        G.add_edge(b, a)

    return G, meta


class OntoRank:
    """Carga grafo + embeddings una vez; rank() responde preguntas del usuario."""

    def __init__(
        self,
        ttl_path: Path = TTL_PATH,
        model_name: str = MODEL_NAME,
        alpha: float = 0.85,
    ):
        # alpha = damping de PageRank (valor del plan)
        self.alpha = alpha
        self.G, self.meta = ttl_a_digraph(ttl_path)
        # Orden estable de nodos para alinear matriz de embeddings
        self.nodes = sorted(self.G.nodes())
        # Textos a embeber: label + cada sinonimo; texto_nodo[j] = indice del nodo
        self.texts, texto_nodo = [], []
        for i, n in enumerate(self.nodes):
            m = self.meta.get(n, {})
            for t in [m.get("label", n), *m.get("sinonimos", [])]:
                self.texts.append(t)
                texto_nodo.append(i)
        self.texto_nodo = np.array(texto_nodo)
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embeddings = self._cargar_o_calcular_embeddings(ttl_path)

    def _cargar_o_calcular_embeddings(self, ttl_path: Path) -> np.ndarray:
        """
        Paso 2 del plan: embeddings de etiqueta (y sinonimos) por nodo.
        Usa cache en disco si el .ttl, el modelo y los textos no cambiaron.
        """
        ttl_mtime = ttl_path.stat().st_mtime
        if EMB_CACHE.exists() and META_CACHE.exists():
            info = json.loads(META_CACHE.read_text(encoding="utf-8"))
            if (
                info.get("model") == self.model_name
                and info.get("ttl_mtime") == ttl_mtime
                and info.get("nodes") == self.nodes
                and info.get("texts") == self.texts
            ):
                return np.load(EMB_CACHE)["embeddings"]

        # Primera vez o cache invalido: encodear todas las etiquetas
        emb = self.model.encode(self.texts, normalize_embeddings=True)
        emb = np.asarray(emb, dtype=np.float32)
        try:
            np.savez_compressed(EMB_CACHE, embeddings=emb)
            META_CACHE.write_text(
                json.dumps(
                    {
                        "model": self.model_name,
                        "ttl_mtime": ttl_mtime,
                        "nodes": self.nodes,
                        "texts": self.texts,
                    }
                ),
                encoding="utf-8",
            )
        except OSError:
            # En Docker ontology/ se monta de solo lectura: se usa el embedding
            # en memoria y se recalcula en el siguiente arranque (~1 s)
            pass
        return emb

    def rank(self, pregunta: str, k: int = 5) -> list[dict]:
        """
        Pasos 3-4 del plan: personalizacion por similitud coseno + PageRank.
        Devuelve top-k de nodos Indicador/ConceptoNoticias (excluye bloques puros)
        con score, fuente y claveAPI.
        """
        # Embeber la pregunta (misma normalizacion L2 que los nodos)
        q = self.model.encode([pregunta], normalize_embeddings=True)[0]
        # Coseno = producto punto si los vectores estan normalizados;
        # cada nodo toma la maxima similitud entre su label y sus sinonimos
        sim_textos = self.embeddings @ q
        sim_nodo = np.full(len(self.nodes), -1.0)
        np.maximum.at(sim_nodo, self.texto_nodo, sim_textos)
        sims = {n: float(sim_nodo[i]) for i, n in enumerate(self.nodes)}
        # Softmax -> vector de personalizacion exigido por pagerank
        personalizacion = _softmax(sims)
        ranking = nx.pagerank(self.G, alpha=self.alpha, personalization=personalizacion)

        # Ordenar por score; filtrar bloques (no tienen serie/API para tools)
        candidatos = [
            (n, score)
            for n, score in ranking.items()
            if self.meta.get(n, {}).get("tipo") in ("Indicador", "ConceptoNoticias")
        ]
        candidatos.sort(key=lambda x: -x[1])

        out = []
        for n, score in candidatos[:k]:
            m = self.meta[n]
            out.append(
                {
                    "id": n,
                    "label": m["label"],
                    "score": round(score, 4),
                    "fuente": m["fuente"],
                    "claveAPI": m["claveAPI"],
                    "unidad": m["unidad"],
                    "frecuencia": m["frecuencia"],
                    "tipo": m["tipo"],
                }
            )
        return out


def main() -> None:
    """Smoke test minimo: rankea una pregunta de ejemplo e imprime top-5."""
    print("Cargando OntoRank (grafo + embeddings)...")
    ranker = OntoRank()
    pregunta = "como va la inflacion en Mexico?"
    print(f"Pregunta: {pregunta}")
    for row in ranker.rank(pregunta, k=5):
        print(row)


if __name__ == "__main__":
    main()
