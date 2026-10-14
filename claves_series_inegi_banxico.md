# Claves de series — INEGI y Banxico

Documento de referencia con las claves consultadas/descargadas en:

- `Consulta_ClaveIndicador_SeriesINEGI.ipynb` (claves BIE)
- `Descarga_SeriesBANXICO.ipynb` (claves SIE)

---

## INEGI (BIE)

Fuente: `Consulta_ClaveIndicador_SeriesINEGI.ipynb`
API: `https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml`

| Clave BIE | Serie / columna en panel |
|---|---|
| `737219` | IGAE Total (`IGAE_Total`) |
| `737226` | IGAE Actividades Primarias (`IGAE_Primarias`) |
| `737233` | IGAE Actividades Secundarias (`IGAE_Secundarias`) |
| `737268` | IGAE Actividades Terciarias (`IGAE_Terciarias`) |
| `736885` | Producción industrial (`Produccion_industrial`) |
| `740987` | Indicador mensual del consumo privado (`Consumo_privado`) |
| `718942` | Ventas al por menor (`Ventas_por_menor`) |
| `87530` | Importaciones de bienes de capital (`Importaciones_bienes_capital`) |
| `444884` | Tasa de desocupación (`Tasa_desocupacion`) |
| `702503` | Horas trabajadas en manufacturas (`Horas_manufacturas`) |
| `87520` | Exportaciones manufactureras (`Exportaciones_manufactureras`) |
| `454186` | Confianza del consumidor (`Confianza_consumidor`) |
| `910454` | Indicador global de opinión empresarial (`Opinion_empresarial`) |
| `436139` | Indicador coincidente del SIC (`Coincidente_SIC`) |
| `436141` | Indicador adelantado del SIC (`Adelantado_SIC`) |
| `334452` | INPC subyacente (`INPC_subyacente`) |
| `910392` | INPC (`INPC`) |
| `334361` | Precios al productor (`Precios_productor`) |
| `720648` | Valor producción total — Edificación (`Valor_produccion_edificacion`) |
| `723135` | Valor producción total — Construcción (`Valor_produccion_construccion`) |
| `724014` | Remuneración de asalariados — total (`Remuneracion_asalariados_total`) |
| `910468` | EMIM volumen físico de producción total (`EMIM_volumen_fisico_produccion_total`) |
| `702671` | EMIM remuneraciones medias reales (`EMIM_remuneraciones_medias_reales`) |
| `668923` | ENOE ocupados sector secundario (`ENOE_ocupados_secundario`) |
| `668927` | ENOE ocupados sector terciario (`ENOE_ocupados_terciario`) |
| `715744` | EMS personal servicios privados no financieros (`EMS_personal_servicios_priv_no_fin`) |
| `718480` | EMEC comercio al por mayor (`EMEC_comercio_por_mayor`) |
| `718482` | EMEC comercio al por menor (`EMEC_comercio_por_menor`) |
| `702106` | IGPOSE (`IGPOSE`) |
| `722254` | ENEC valor producción subsector 236 — Edificación (`ENEC_valor_produccion_subsector_236`) |
| `722255` | ENEC valor producción subsector 237 — Ingeniería civil (`ENEC_valor_produccion_subsector_237`) |
| `720326` | ENEC valor producción sector 23 — Construcción (`ENEC_valor_produccion_sector_23`) |
| `910499` | INPP minería sin petróleo (`INPP_mineria_sin_petroleo`) |
| `910500` | INPP minería con petróleo (`INPP_mineria_con_petroleo`) |
| `910498` | INPP agricultura, silvicultura y pesca (`INPP_agricultura_forestal_pesca`) |
| `910492` | INPP con petróleo y servicios (`INPP_con_petroleo_servicios`) |
| `910491` | INPP sin petróleo y servicios (`INPP_sin_petroleo_servicios`) |
| `910501` | INPP energía eléctrica, agua y gas (`INPP_energia_electrica_agua_gas`) |
| `702127` | IGRESE (`IGRESE`) |
| `702134` | IGREMSE (`IGREMSE`) |
| `441566` | Impuestos (consultada en metadatos; no figura como columna del panel actual) |

**Total consultadas:** 41 claves.

---

## Banxico (SIE)

Fuente: `Descarga_SeriesBANXICO.ipynb`
API: `https://www.banxico.org.mx/SieAPIRest/service/v1`

| Clave SIE | Serie / columna en panel |
|---|---|
| `SF61745` | Tasa objetivo (`Tasa_objetivo`) |
| `SF60633` | CETES 28 días (`CETES_28_dias`) |
| `SF60634` | CETES 91 días (`CETES_91_dias`) |
| `SF60635` | CETES 182 días (`CETES_182_dias`) |
| `SF60636` | CETES 364 días (`CETES_364_dias`) |
| `SF43783` | TIIE 28 días (`TIIE_28_dias`) |
| `SF60640` | Mbono tasa fija 3 años (`Mbono_tasa_fija_3y`) |
| `SF60641` | Mbono tasa fija 5 años (`Mbono_tasa_fija_5y`) |
| `SF60643` | Mbono tasa fija 10 años (`Mbono_tasa_fija_10y`) |
| `SF311408` | Agregado monetario M1 (`M1`) |
| `SF311418` | Agregado monetario M2 (`M2`) |
| `SF311433` | Agregado monetario M3 (`M3`) |
| `SF311438` | Agregado monetario M4 (`M4`) |
| `SF235704` | Crédito real al sector privado (`Credito_real_sector_privado`) |
| `SF235705` | Crédito al consumo (`Credito_consumo`) |
| `SF235707` | Crédito a la vivienda — banca comercial (`Credito_vivienda_banca_comercial`) |
| `SF235708` | Crédito a empresas — actividad empresarial (`Credito_empresas_actividad_empresarial`) |
| `SF43718` | Tipo de cambio FIX (`TC_FIX`) |
| `SF43716` | IPC bolsa (`IPC_bolsa`) |
| `SF106800` | Remesas reales deflactadas con INPC (`Remesas_reales_INPC`) |
| `SF276064` | Monto total de transferencias SPEI (`SPEI_monto_total_pesos`) |
| `SF42525` | Cuentas o contratos con tarjeta de crédito (`Cuentas_tarjeta_credito`) |
| `SR14195` | Expectativa de inflación general a 12 meses — mediana (`EE_inflacion_general_prox12m_mediana`) |
| `SR14448` | Expectativa de PIB real anual — mediana año t (`EE_PIB_real_anual_mediana_año_t`) |
| `SR14770` | Expectativa de tipo de cambio al cierre del año — mediana (`EE_TC_pesos_dolar_cierre_año_t_mediana`) |
| `SG10` | Ingresos tributarios totales del Gobierno Federal — CG2 (`Ingresos_tributarios_totales_GF_CG2_millones_pesos`) |

**Total descargadas:** 26 claves.
