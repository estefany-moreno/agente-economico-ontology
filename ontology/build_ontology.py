"""
build_ontology.py
-----------------
Construye el grafo RDF/Turtle de la ontologia economica del proyecto
(capa descrita en plan_de_trabajo.md, seccion 1).

Que hace este script (una sola vez, o cada vez que se edite el inventario):
1. Declara el namespace, clases y propiedades RDF con rdflib.
2. Carga los 66 indicadores (40 INEGI + 26 Banxico) organizados en bloques.
3. Agrega un concepto de tipo Noticias (cuarto tipo de fuente / concepto).
4. Escribe ontology/indicadores.ttl (metadatos publicos; sin tokens ni secretos).

Uso (desde la raiz del repo, con el environment activo):
    python ontology/build_ontology.py

Dependencia: rdflib
"""

from __future__ import annotations

# pathlib: rutas portables al archivo .ttl de salida
from pathlib import Path

# rdflib: grafo RDF, namespaces, serializacion Turtle
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import SKOS, XSD


# ---------------------------------------------------------------------------
# Rutas: el .ttl vive junto a este script, versionado en el repo
# ---------------------------------------------------------------------------
ONTOLOGY_DIR = Path(__file__).resolve().parent
OUTPUT_TTL = ONTOLOGY_DIR / "indicadores.ttl"

# Namespace local del proyecto (URI estable para nodos y propiedades)
AE = Namespace("http://agente-economico.local/ontologia#")


# ---------------------------------------------------------------------------
# Inventario de bloques (marco tipo Stock & Watson del panel)
# id interno -> etiqueta legible en espanol
# ---------------------------------------------------------------------------
BLOQUES: dict[str, str] = {
    "BloqueProduccion": "Produccion e ingreso real",
    "BloqueEmpleo": "Empleo y mercado laboral",
    "BloqueConsumo": "Consumo",
    "BloqueVivienda": "Vivienda y Construccion",
    "BloquePrecios": "Precios",
    "BloqueSalarios": "Salarios y costos laborales",
    "BloqueTasas": "Tasas de interes",
    "BloqueDineroCredito": "Dinero y credito",
    "BloqueTipoCambio": "Tipo de cambio",
    "BloqueBursatil": "Mercado bursatil",
    "BloqueExpectativas": "Expectativas y sentimiento",
    "BloqueGobierno": "Sector gobierno",
    "BloqueFinancierosExternos": "Indicadores financieros y externos",
}


# ---------------------------------------------------------------------------
# Fuentes (nodos individuales; el plan: INEGI | Banxico | Noticias)
# ---------------------------------------------------------------------------
FUENTES: dict[str, str] = {
    "INEGI": "Instituto Nacional de Estadistica y Geografia",
    "Banxico": "Banco de Mexico (SIE)",
    "Noticias": "Noticias economicas y financieras (Google Sheets / recoleccion)",
}


# ---------------------------------------------------------------------------
# Indicadores: cada entrada alimenta un nodo :Indicador en el grafo.
#
# Campos:
#   id          -> nombre de columna en panel / URI local del nodo
#   label       -> rdfs:label en espanol
#   bloque      -> clave en BLOQUES (:perteneceABloque)
#   fuente      -> "INEGI" | "Banxico" (:fuente)
#   clave_api   -> ID publico de la serie en INEGI BIE o Banxico SIE.
#                  Vacio "" si aun no se ha cargado desde los notebooks;
#                  no es un secreto, es el identificador de indicador.
#   frecuencia  -> periodicidad de la fuente (mensual / trimestral / anual)
#   unidad      -> unidad o descripcion corta (editable)
#   sinonimos   -> (opcional) terminos coloquiales -> skos:altLabel; OntoRank
#                  los embebe junto al label (p. ej. "inflacion" -> INPC)
#
# Totales esperados: 66 (40 INEGI + 26 Banxico).
# ---------------------------------------------------------------------------
INDICADORES: list[dict[str, str]] = [
    # --- Bloque 1 — Produccion e ingreso real (INEGI, 6) ---
    {
        "id": "IGAE_Total",
        "label": "Indicador Global de Actividad Economica — total",
        "bloque": "BloqueProduccion",
        "fuente": "INEGI",
        "clave_api": "737219",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "IGAE_Primarias",
        "label": "IGAE — actividades primarias",
        "bloque": "BloqueProduccion",
        "fuente": "INEGI",
        "clave_api": "737226",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "IGAE_Secundarias",
        "label": "IGAE — actividades secundarias",
        "bloque": "BloqueProduccion",
        "fuente": "INEGI",
        "clave_api": "737233",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "IGAE_Terciarias",
        "label": "IGAE — actividades terciarias",
        "bloque": "BloqueProduccion",
        "fuente": "INEGI",
        "clave_api": "737268",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "Produccion_industrial",
        "label": "Indice de produccion industrial",
        "bloque": "BloqueProduccion",
        "fuente": "INEGI",
        "clave_api": "736885",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "EMIM_volumen_fisico_produccion_total",
        "label": "EMIM — volumen fisico de produccion (total)",
        "bloque": "BloqueProduccion",
        "fuente": "INEGI",
        "clave_api": "910468",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    # --- Bloque 2 — Empleo y mercado laboral (INEGI, 10) ---
    {
        "id": "Tasa_desocupacion",
        "label": "Tasa de desocupacion nacional (ENOE)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "444884",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "Horas_manufacturas",
        "label": "Horas trabajadas en manufacturas (EMIM)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "702503",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "ENOE_ocupados_secundario",
        "label": "Ocupados en el sector secundario (ENOE)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "668923",
        "frecuencia": "mensual",
        "unidad": "personas",
    },
    {
        "id": "ENOE_ocupados_terciario",
        "label": "Ocupados en el sector terciario (ENOE)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "668927",
        "frecuencia": "mensual",
        "unidad": "personas",
    },
    {
        "id": "EMS_personal_servicios_priv_no_fin",
        "label": "Personal ocupado en servicios privados no financieros (EMS)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "715744",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "EMEC_comercio_por_mayor",
        "label": "Personal ocupado en comercio al por mayor (EMEC)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "718480",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "EMEC_comercio_por_menor",
        "label": "Personal ocupado en comercio al por menor (EMEC)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "718482",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "IGPOSE",
        "label": "Indice global de personal ocupado en establecimientos (IGPOSE)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "702106",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "IGRESE",
        "label": "Indice global de remuneraciones en establecimientos (IGRESE)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "702127",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "IGREMSE",
        "label": "Indice global de remuneraciones medias en establecimientos (IGREMSE)",
        "bloque": "BloqueEmpleo",
        "fuente": "INEGI",
        "clave_api": "702134",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    # --- Bloque 3 — Consumo (INEGI, 2) ---
    {
        "id": "Consumo_privado",
        "label": "Indicador mensual del consumo privado en el mercado interior",
        "bloque": "BloqueConsumo",
        "fuente": "INEGI",
        "clave_api": "740987",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "Ventas_por_menor",
        "label": "Ventas al por menor (comercio minorista)",
        "bloque": "BloqueConsumo",
        "fuente": "INEGI",
        "clave_api": "718942",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    # --- Bloque 4 — Vivienda y Construccion (INEGI 5 + Banxico 1) ---
    {
        "id": "ENEC_valor_produccion_subsector_236",
        "label": "Valor de produccion de edificacion — subsector 236 (ENEC)",
        "bloque": "BloqueVivienda",
        "fuente": "INEGI",
        "clave_api": "722254",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "ENEC_valor_produccion_subsector_237",
        "label": "Valor de produccion de ingenieria civil — subsector 237 (ENEC)",
        "bloque": "BloqueVivienda",
        "fuente": "INEGI",
        "clave_api": "722255",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "ENEC_valor_produccion_sector_23",
        "label": "Valor de produccion del sector construccion — sector 23 (ENEC)",
        "bloque": "BloqueVivienda",
        "fuente": "INEGI",
        "clave_api": "720326",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "Valor_produccion_edificacion",
        "label": "Valor total de produccion — edificacion",
        "bloque": "BloqueVivienda",
        "fuente": "INEGI",
        "clave_api": "720648",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "Valor_produccion_construccion",
        "label": "Valor total de produccion — construccion",
        "bloque": "BloqueVivienda",
        "fuente": "INEGI",
        "clave_api": "723135",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "Credito_vivienda_banca_comercial",
        "label": "Cartera de credito a la vivienda — banca comercial",
        "bloque": "BloqueVivienda",
        "fuente": "Banxico",
        "clave_api": "SF235707",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    # --- Bloque 5 — Precios (INEGI, 9) ---
    {
        "id": "INPC",
        "label": "Indice Nacional de Precios al Consumidor (INPC)",
        "bloque": "BloquePrecios",
        "fuente": "INEGI",
        "clave_api": "910392",
        "frecuencia": "mensual",
        "unidad": "indice",
        "sinonimos": [
            "inflacion",
            "inflacion general",
            "inflacion anual",
            "tasa de inflacion",
            "inflacion al consumidor",
            "precios al consumidor",
            "aumento de precios",
            "costo de vida",
            "carestia",
        ],
    },
    {
        "id": "INPC_subyacente",
        "label": "INPC subyacente",
        "bloque": "BloquePrecios",
        "fuente": "INEGI",
        "clave_api": "334452",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "Precios_productor",
        "label": "Indice de precios al productor (serie general)",
        "bloque": "BloquePrecios",
        "fuente": "INEGI",
        "clave_api": "334361",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "INPP_mineria_sin_petroleo",
        "label": "INPP — mineria sin petroleo",
        "bloque": "BloquePrecios",
        "fuente": "INEGI",
        "clave_api": "910499",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "INPP_mineria_con_petroleo",
        "label": "INPP — mineria con petroleo",
        "bloque": "BloquePrecios",
        "fuente": "INEGI",
        "clave_api": "910500",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "INPP_agricultura_forestal_pesca",
        "label": "INPP — agricultura, silvicultura y pesca",
        "bloque": "BloquePrecios",
        "fuente": "INEGI",
        "clave_api": "910498",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "INPP_con_petroleo_servicios",
        "label": "INPP — con petroleo y servicios",
        "bloque": "BloquePrecios",
        "fuente": "INEGI",
        "clave_api": "910492",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "INPP_sin_petroleo_servicios",
        "label": "INPP — sin petroleo y servicios",
        "bloque": "BloquePrecios",
        "fuente": "INEGI",
        "clave_api": "910491",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "INPP_energia_electrica_agua_gas",
        "label": "INPP — energia electrica, agua y gas",
        "bloque": "BloquePrecios",
        "fuente": "INEGI",
        "clave_api": "910501",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    # --- Bloque 6 — Salarios y costos laborales (INEGI, 2) ---
    # clave_api conocida en documentacion del panel: BIE 724014 (anual en fuente)
    {
        "id": "Remuneracion_asalariados_total",
        "label": "Remuneracion de asalariados — total",
        "bloque": "BloqueSalarios",
        "fuente": "INEGI",
        "clave_api": "724014",
        "frecuencia": "anual",
        "unidad": "millones de pesos",
    },
    {
        "id": "EMIM_remuneraciones_medias_reales",
        "label": "Remuneraciones medias reales — total (EMIM)",
        "bloque": "BloqueSalarios",
        "fuente": "INEGI",
        "clave_api": "702671",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    # --- Bloque 7 — Tasas de interes (Banxico, 9) ---
    {
        "id": "Tasa_objetivo",
        "label": "Tasa de interes objetivo del Banco de Mexico",
        "bloque": "BloqueTasas",
        "fuente": "Banxico",
        "clave_api": "SF61745",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "CETES_28_dias",
        "label": "CETES a 28 dias (rendimiento en subasta)",
        "bloque": "BloqueTasas",
        "fuente": "Banxico",
        "clave_api": "SF60633",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "CETES_91_dias",
        "label": "CETES a 91 dias (rendimiento en subasta)",
        "bloque": "BloqueTasas",
        "fuente": "Banxico",
        "clave_api": "SF60634",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "CETES_182_dias",
        "label": "CETES a 182 dias (rendimiento en subasta)",
        "bloque": "BloqueTasas",
        "fuente": "Banxico",
        "clave_api": "SF60635",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "CETES_364_dias",
        "label": "CETES a 364 dias (rendimiento en subasta)",
        "bloque": "BloqueTasas",
        "fuente": "Banxico",
        "clave_api": "SF60636",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "TIIE_28_dias",
        "label": "TIIE a 28 dias",
        "bloque": "BloqueTasas",
        "fuente": "Banxico",
        "clave_api": "SF43783",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "Mbono_tasa_fija_3y",
        "label": "Bono gubernamental a tasa fija — rendimiento 3 anos",
        "bloque": "BloqueTasas",
        "fuente": "Banxico",
        "clave_api": "SF60640",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "Mbono_tasa_fija_5y",
        "label": "Bono gubernamental a tasa fija — rendimiento 5 anos",
        "bloque": "BloqueTasas",
        "fuente": "Banxico",
        "clave_api": "SF60641",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "Mbono_tasa_fija_10y",
        "label": "Bono gubernamental a tasa fija — rendimiento 10 anos",
        "bloque": "BloqueTasas",
        "fuente": "Banxico",
        "clave_api": "SF60643",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    # --- Bloque 8 — Dinero y credito (Banxico, 7) ---
    {
        "id": "M1",
        "label": "Agregado monetario M1",
        "bloque": "BloqueDineroCredito",
        "fuente": "Banxico",
        "clave_api": "SF311408",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "M2",
        "label": "Agregado monetario M2",
        "bloque": "BloqueDineroCredito",
        "fuente": "Banxico",
        "clave_api": "SF311418",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "M3",
        "label": "Agregado monetario M3",
        "bloque": "BloqueDineroCredito",
        "fuente": "Banxico",
        "clave_api": "SF311433",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "M4",
        "label": "Agregado monetario M4",
        "bloque": "BloqueDineroCredito",
        "fuente": "Banxico",
        "clave_api": "SF311438",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "Credito_real_sector_privado",
        "label": "Credito real al sector privado — cartera total",
        "bloque": "BloqueDineroCredito",
        "fuente": "Banxico",
        "clave_api": "SF235704",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "Credito_consumo",
        "label": "Cartera de credito al consumo",
        "bloque": "BloqueDineroCredito",
        "fuente": "Banxico",
        "clave_api": "SF235705",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    {
        "id": "Credito_empresas_actividad_empresarial",
        "label": "Cartera de credito a empresas (actividad empresarial)",
        "bloque": "BloqueDineroCredito",
        "fuente": "Banxico",
        "clave_api": "SF235708",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    # --- Bloque 9 — Tipo de cambio (Banxico, 2) ---
    {
        "id": "TC_FIX",
        "label": "Tipo de cambio FIX (peso por dolar estadounidense)",
        "bloque": "BloqueTipoCambio",
        "fuente": "Banxico",
        "clave_api": "SF43718",
        "frecuencia": "mensual",
        "unidad": "pesos por dolar",
    },
    {
        "id": "EE_TC_pesos_dolar_cierre_año_t_mediana",
        "label": "Expectativa de tipo de cambio al cierre del ano (mediana)",
        "bloque": "BloqueTipoCambio",
        "fuente": "Banxico",
        "clave_api": "SR14770",
        "frecuencia": "mensual",
        "unidad": "pesos por dolar",
    },
    # --- Bloque 10 — Mercado bursatil (Banxico, 1) ---
    {
        "id": "IPC_bolsa",
        "label": "Indice de Precios y Cotizaciones de la BMV (IPC)",
        "bloque": "BloqueBursatil",
        "fuente": "Banxico",
        "clave_api": "SF43716",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    # --- Bloque 11 — Expectativas y sentimiento (INEGI 2 + Banxico 2) ---
    {
        "id": "Confianza_consumidor",
        "label": "Indicador de confianza del consumidor (ENCO)",
        "bloque": "BloqueExpectativas",
        "fuente": "INEGI",
        "clave_api": "454186",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "Opinion_empresarial",
        "label": "Indicador global de opinion empresarial (IGOE / EMOE)",
        "bloque": "BloqueExpectativas",
        "fuente": "INEGI",
        "clave_api": "910454",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "EE_inflacion_general_prox12m_mediana",
        "label": "Expectativa de inflacion general a 12 meses (mediana)",
        "bloque": "BloqueExpectativas",
        "fuente": "Banxico",
        "clave_api": "SR14195",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    {
        "id": "EE_PIB_real_anual_mediana_año_t",
        "label": "Expectativa de variacion del PIB real anual (mediana; ano en curso)",
        "bloque": "BloqueExpectativas",
        "fuente": "Banxico",
        "clave_api": "SR14448",
        "frecuencia": "mensual",
        "unidad": "porcentaje",
    },
    # --- Bloque 12 — Sector gobierno (Banxico, 1) ---
    {
        "id": "Ingresos_tributarios_totales_GF_CG2_millones_pesos",
        "label": "Ingreso total tributarios del Gobierno Federal (CG2)",
        "bloque": "BloqueGobierno",
        "fuente": "Banxico",
        "clave_api": "SG10",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    # --- Bloque 13 — Indicadores financieros y externos (INEGI 4 + Banxico 3) ---
    {
        "id": "Importaciones_bienes_capital",
        "label": "Importaciones de bienes de capital",
        "bloque": "BloqueFinancierosExternos",
        "fuente": "INEGI",
        "clave_api": "87530",
        "frecuencia": "mensual",
        "unidad": "millones de dolares",
    },
    {
        "id": "Exportaciones_manufactureras",
        "label": "Exportaciones manufactureras",
        "bloque": "BloqueFinancierosExternos",
        "fuente": "INEGI",
        "clave_api": "87520",
        "frecuencia": "mensual",
        "unidad": "millones de dolares",
    },
    {
        "id": "Remesas_reales_INPC",
        "label": "Remesas familiares deflactadas (reales, INPC)",
        "bloque": "BloqueFinancierosExternos",
        "fuente": "Banxico",
        "clave_api": "SF106800",
        "frecuencia": "mensual",
        "unidad": "millones de pesos reales",
    },
    {
        "id": "SPEI_monto_total_pesos",
        "label": "Monto total de transferencias SPEI",
        "bloque": "BloqueFinancierosExternos",
        "fuente": "Banxico",
        "clave_api": "SF276064",
        "frecuencia": "mensual",
        "unidad": "millones de pesos",
    },
    # clave_api documentada en el panel: SF42525 (trimestral en SIE)
    {
        "id": "Cuentas_tarjeta_credito",
        "label": "Cuentas o contratos con tarjeta de credito",
        "bloque": "BloqueFinancierosExternos",
        "fuente": "Banxico",
        "clave_api": "SF42525",
        "frecuencia": "trimestral",
        "unidad": "cuentas",
    },
    {
        "id": "Coincidente_SIC",
        "label": "Indicador coincidente del SIC",
        "bloque": "BloqueFinancierosExternos",
        "fuente": "INEGI",
        "clave_api": "436139",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
    {
        "id": "Adelantado_SIC",
        "label": "Indicador adelantado del SIC",
        "bloque": "BloqueFinancierosExternos",
        "fuente": "INEGI",
        "clave_api": "436141",
        "frecuencia": "mensual",
        "unidad": "indice",
    },
]


# ---------------------------------------------------------------------------
# Relaciones economicas :relacionadoCon
# Semilla inicial con los ejemplos del plan y aristas claras dentro del panel.
# El plan indica que el valor agregado esta en refinar estas aristas con
# criterio economico; editar esta lista y regenerar el .ttl.
# Formato: (origen_id, destino_id)
# ---------------------------------------------------------------------------
RELACIONES: list[tuple[str, str]] = [
    # Ejemplos explicitos del plan
    ("INPC", "INPC_subyacente"),
    ("Tasa_objetivo", "CETES_28_dias"),
    # Precios
    ("INPC", "Precios_productor"),
    ("INPC", "EE_inflacion_general_prox12m_mediana"),
    ("INPP_con_petroleo_servicios", "INPP_sin_petroleo_servicios"),
    # Produccion
    ("IGAE_Total", "IGAE_Primarias"),
    ("IGAE_Total", "IGAE_Secundarias"),
    ("IGAE_Total", "IGAE_Terciarias"),
    ("IGAE_Secundarias", "Produccion_industrial"),
    ("Produccion_industrial", "EMIM_volumen_fisico_produccion_total"),
    ("IGAE_Total", "Coincidente_SIC"),
    ("Adelantado_SIC", "Coincidente_SIC"),
    # Empleo y salarios
    ("Tasa_desocupacion", "ENOE_ocupados_secundario"),
    ("Tasa_desocupacion", "ENOE_ocupados_terciario"),
    ("IGPOSE", "IGRESE"),
    ("IGRESE", "IGREMSE"),
    ("Horas_manufacturas", "EMIM_remuneraciones_medias_reales"),
    # Consumo
    ("Consumo_privado", "Ventas_por_menor"),
    ("Confianza_consumidor", "Consumo_privado"),
    # Vivienda / construccion
    ("ENEC_valor_produccion_sector_23", "ENEC_valor_produccion_subsector_236"),
    ("ENEC_valor_produccion_sector_23", "ENEC_valor_produccion_subsector_237"),
    ("Valor_produccion_construccion", "Credito_vivienda_banca_comercial"),
    # Tasas y dinero
    ("Tasa_objetivo", "TIIE_28_dias"),
    ("CETES_28_dias", "CETES_91_dias"),
    ("CETES_91_dias", "CETES_182_dias"),
    ("CETES_182_dias", "CETES_364_dias"),
    ("Mbono_tasa_fija_3y", "Mbono_tasa_fija_5y"),
    ("Mbono_tasa_fija_5y", "Mbono_tasa_fija_10y"),
    ("M1", "M2"),
    ("M2", "M3"),
    ("M3", "M4"),
    ("Credito_real_sector_privado", "Credito_consumo"),
    ("Credito_real_sector_privado", "Credito_empresas_actividad_empresarial"),
    ("Credito_consumo", "Cuentas_tarjeta_credito"),
    # Tipo de cambio y externos
    ("TC_FIX", "EE_TC_pesos_dolar_cierre_año_t_mediana"),
    ("Exportaciones_manufactureras", "Importaciones_bienes_capital"),
    ("Remesas_reales_INPC", "INPC"),
    # Expectativas
    ("Opinion_empresarial", "EE_PIB_real_anual_mediana_año_t"),
    ("Confianza_consumidor", "EE_inflacion_general_prox12m_mediana"),
]


def _uri(local_name: str) -> URIRef:
    """Construye la URI local AE#local_name para un nodo o propiedad."""
    return AE[local_name]


def _validar_inventario() -> None:
    """
    Comprueba conteos y referencias antes de escribir el grafo.
    Falla temprano si hay inconsistencias (ids duplicados, relaciones rotas).
    """
    ids = [ind["id"] for ind in INDICADORES]
    if len(ids) != len(set(ids)):
        raise ValueError("Hay ids de indicador duplicados en INDICADORES.")

    n = len(INDICADORES)
    if n != 66:
        raise ValueError(f"Se esperaban 66 indicadores; hay {n}.")

    n_inegi = sum(1 for ind in INDICADORES if ind["fuente"] == "INEGI")
    n_banxico = sum(1 for ind in INDICADORES if ind["fuente"] == "Banxico")
    if n_inegi != 40 or n_banxico != 26:
        raise ValueError(
            f"Conteo por fuente incorrecto: INEGI={n_inegi} (esperado 40), "
            f"Banxico={n_banxico} (esperado 26)."
        )

    id_set = set(ids)
    for origen, destino in RELACIONES:
        if origen not in id_set or destino not in id_set:
            raise ValueError(
                f"Relacion invalida: {origen} -> {destino} "
                "(algun id no existe en INDICADORES)."
            )

    for ind in INDICADORES:
        if ind["bloque"] not in BLOQUES:
            raise ValueError(
                f"Bloque desconocido '{ind['bloque']}' en indicador {ind['id']}."
            )
        if ind["fuente"] not in FUENTES:
            raise ValueError(
                f"Fuente desconocida '{ind['fuente']}' en indicador {ind['id']}."
            )


def construir_grafo() -> Graph:
    """
    Arma el grafo RDF completo:
    - bind de namespaces
    - clases (Indicador, Bloque, Fuente, ConceptoNoticias)
    - propiedades (perteneceABloque, fuente, claveAPI, frecuencia, unidad, relacionadoCon)
    - instancias de bloques, fuentes, 66 indicadores, concepto Noticias
    - aristas relacionadoCon
    """
    g = Graph()

    # Prefijos legibles en el Turtle de salida
    g.bind("ae", AE)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)
    g.bind("skos", SKOS)

    # --- Clases ---
    # Indicador: serie del panel (nodo principal para OntoRank)
    g.add((_uri("Indicador"), RDF.type, RDFS.Class))
    g.add((_uri("Indicador"), RDFS.label, Literal("Indicador economico", lang="es")))

    # Bloque: agrupacion tematica tipo Stock & Watson
    g.add((_uri("Bloque"), RDF.type, RDFS.Class))
    g.add((_uri("Bloque"), RDFS.label, Literal("Bloque tematico", lang="es")))

    # Fuente: INEGI, Banxico o Noticias
    g.add((_uri("Fuente"), RDF.type, RDFS.Class))
    g.add((_uri("Fuente"), RDFS.label, Literal("Fuente de datos", lang="es")))

    # ConceptoNoticias: cuarto tipo de concepto (plan seccion 1), no es serie de panel
    g.add((_uri("ConceptoNoticias"), RDF.type, RDFS.Class))
    g.add(
        (
            _uri("ConceptoNoticias"),
            RDFS.label,
            Literal("Concepto de noticias economicas", lang="es"),
        )
    )

    # --- Propiedades (objeto o dato) ---
    props = {
        "perteneceABloque": "Indicador pertenece a un bloque tematico",
        "fuente": "Fuente de la serie o concepto (INEGI | Banxico | Noticias)",
        "claveAPI": "Identificador publico de la serie en la API de origen",
        "frecuencia": "Periodicidad de la fuente",
        "unidad": "Unidad de medida o descripcion corta",
        "relacionadoCon": "Relacion economica entre indicadores (arista para OntoRank)",
    }
    for prop_name, prop_label in props.items():
        prop = _uri(prop_name)
        g.add((prop, RDF.type, RDF.Property))
        g.add((prop, RDFS.label, Literal(prop_label, lang="es")))

    # --- Instancias de bloques ---
    for bloque_id, bloque_label in BLOQUES.items():
        nodo = _uri(bloque_id)
        g.add((nodo, RDF.type, _uri("Bloque")))
        g.add((nodo, RDFS.label, Literal(bloque_label, lang="es")))

    # --- Instancias de fuentes ---
    for fuente_id, fuente_label in FUENTES.items():
        nodo = _uri(fuente_id)
        g.add((nodo, RDF.type, _uri("Fuente")))
        g.add((nodo, RDFS.label, Literal(fuente_label, lang="es")))

    # --- 66 indicadores ---
    for ind in INDICADORES:
        nodo = _uri(ind["id"])
        g.add((nodo, RDF.type, _uri("Indicador")))
        g.add((nodo, RDFS.label, Literal(ind["label"], lang="es")))
        g.add((nodo, _uri("perteneceABloque"), _uri(ind["bloque"])))
        g.add((nodo, _uri("fuente"), _uri(ind["fuente"])))
        # claveAPI puede ir vacia hasta completar el inventario desde notebooks
        g.add(
            (
                nodo,
                _uri("claveAPI"),
                Literal(ind["clave_api"], datatype=XSD.string),
            )
        )
        g.add(
            (
                nodo,
                _uri("frecuencia"),
                Literal(ind["frecuencia"], datatype=XSD.string),
            )
        )
        g.add(
            (
                nodo,
                _uri("unidad"),
                Literal(ind["unidad"], datatype=XSD.string),
            )
        )
        # Sinonimos coloquiales (estandar SKOS) para el matching semantico
        for sinonimo in ind.get("sinonimos", []):
            g.add((nodo, SKOS.altLabel, Literal(sinonimo, lang="es")))

    # --- Concepto de noticias (cuarto tipo; fuente Noticias) ---
    noticias = _uri("Noticias_economicas")
    g.add((noticias, RDF.type, _uri("ConceptoNoticias")))
    g.add(
        (
            noticias,
            RDFS.label,
            Literal(
                "Noticias economicas y financieras de Mexico (indice de sentimiento)",
                lang="es",
            ),
        )
    )
    g.add((noticias, _uri("fuente"), _uri("Noticias")))
    g.add((noticias, _uri("frecuencia"), Literal("diaria", datatype=XSD.string)))
    g.add(
        (
            noticias,
            _uri("unidad"),
            Literal("texto / indice de sentimiento", datatype=XSD.string),
        )
    )
    # Vinculo suave con expectativas: las noticias informan sentimiento
    g.add((noticias, _uri("relacionadoCon"), _uri("Confianza_consumidor")))
    g.add((noticias, _uri("relacionadoCon"), _uri("Opinion_empresarial")))

    # --- Aristas relacionadoCon entre indicadores ---
    for origen, destino in RELACIONES:
        g.add((_uri(origen), _uri("relacionadoCon"), _uri(destino)))

    return g


def escribir_ttl(grafo: Graph, ruta: Path = OUTPUT_TTL) -> None:
    """Serializa el grafo a Turtle (.ttl) en la ruta indicada."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    grafo.serialize(destination=str(ruta), format="turtle")


def main() -> None:
    """Punto de entrada: validar inventario, construir grafo, escribir .ttl."""
    print("Validando inventario de indicadores...")
    _validar_inventario()

    print("Construyendo grafo RDF con rdflib...")
    grafo = construir_grafo()

    print(f"Escribiendo ontologia en: {OUTPUT_TTL}")
    escribir_ttl(grafo)

    n_ind = sum(
        1
        for s, p, o in grafo.triples((None, RDF.type, _uri("Indicador")))
    )
    n_rel = sum(
        1
        for s, p, o in grafo.triples((None, _uri("relacionadoCon"), None))
    )
    print(f"Listo. Indicadores: {n_ind}. Triplets relacionadoCon: {n_rel}.")
    print(f"Triplets totales en el grafo: {len(grafo)}.")


if __name__ == "__main__":
    main()
