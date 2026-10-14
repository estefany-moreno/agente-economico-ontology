# Información del panel — `panel_series.csv`

Documento de referencia para las **series presentes** en `Panel_datos/panel_series.csv` (salida de `Creacion_panel.ipynb`) cuya fuente es **INEGI** o **Banxico**.

- **Índice temporal:** columna `fecha` (primer día de mes, mensual).
- **Fuentes de descarga / integración:** se indica el origen principal (notebook o carpeta de integración).

**Totales:** 66 variables de panel (además de `fecha`). Quedan listadas en los **bloques 1 a 13** (marco tipo Stock & Watson).

---

### Bloque 1 — Producción e ingreso real

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Indicador Global de Actividad Económica — total | `IGAE_Total` | INEGI — `Descarga_SeriesINEGI.ipynb` → `series_inegi.csv` |
| IGAE — actividades primarias | `IGAE_Primarias` | INEGI — `series_inegi.csv` |
| IGAE — actividades secundarias | `IGAE_Secundarias` | INEGI — `series_inegi.csv` |
| IGAE — actividades terciarias | `IGAE_Terciarias` | INEGI — `series_inegi.csv` |
| Índice de producción industrial | `Produccion_industrial` | INEGI — `series_inegi.csv` |
| EMIM — volumen físico de producción (total) | `EMIM_volumen_fisico_produccion_total` | INEGI — `series_inegi.csv` |

---

### Bloque 2 — Empleo y mercado laboral

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Tasa de desocupación nacional (ENOE, serie en panel INEGI) | `Tasa_desocupacion` | INEGI — `series_inegi.csv` |
| Horas trabajadas en manufacturas (EMIM) | `Horas_manufacturas` | INEGI — `series_inegi.csv` |
| Ocupados en el sector secundario (ENOE) | `ENOE_ocupados_secundario` | INEGI — `series_inegi.csv` |
| Ocupados en el sector terciario (ENOE) | `ENOE_ocupados_terciario` | INEGI — `series_inegi.csv` |
| Personal ocupado en servicios privados no financieros (EMS) | `EMS_personal_servicios_priv_no_fin` | INEGI — `series_inegi.csv` |
| Personal ocupado en comercio al por mayor (EMEC) | `EMEC_comercio_por_mayor` | INEGI — `series_inegi.csv` |
| Personal ocupado en comercio al por menor (EMEC) | `EMEC_comercio_por_menor` | INEGI — `series_inegi.csv` |
| Índice global de personal ocupado en establecimientos (IGPOSE) | `IGPOSE` | INEGI — `series_inegi.csv` |
| Índice global de remuneraciones en establecimientos (IGRESE) | `IGRESE` | INEGI — `series_inegi.csv` |
| Índice global de remuneraciones medias en establecimientos (IGREMSE) | `IGREMSE` | INEGI — `series_inegi.csv` |

---

### Bloque 3 — Consumo

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Indicador mensual del consumo privado en el mercado interior | `Consumo_privado` | INEGI — `series_inegi.csv` |
| Ventas al por menor (comercio minorista) | `Ventas_por_menor` | INEGI — `series_inegi.csv` |

---

### Bloque 4 — Vivienda y Construcción

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Valor de producción de edificación — subsector 236 (ENEC) | `ENEC_valor_produccion_subsector_236` | INEGI — `series_inegi.csv` |
| Valor de producción de ingeniería civil — subsector 237 (ENEC) | `ENEC_valor_produccion_subsector_237` | INEGI — `series_inegi.csv` |
| Valor de producción del sector construcción — sector 23 (ENEC) | `ENEC_valor_produccion_sector_23` | INEGI — `series_inegi.csv` |
| Valor total de producción — edificación (serie de actividad) | `Valor_produccion_edificacion` | INEGI — `series_inegi.csv` |
| Valor total de producción — construcción (serie de actividad) | `Valor_produccion_construccion` | INEGI — `series_inegi.csv` |
| Cartera de crédito a la vivienda — banca comercial | `Credito_vivienda_banca_comercial` | Banxico — SIE — `series_banxico.csv` (`Descarga_SeriesBANXICO.ipynb`) |

---

### Bloque 5 — Precios

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Índice Nacional de Precios al Consumidor (INPC) | `INPC` | INEGI — `series_inegi.csv` |
| INPC subyacente | `INPC_subyacente` | INEGI — `series_inegi.csv` |
| Índice de precios al productor (serie general) | `Precios_productor` | INEGI — `series_inegi.csv` |
| INPP — minería sin petróleo | `INPP_mineria_sin_petroleo` | INEGI — `series_inegi.csv` |
| INPP — minería con petróleo | `INPP_mineria_con_petroleo` | INEGI — `series_inegi.csv` |
| INPP — agricultura, silvicultura y pesca | `INPP_agricultura_forestal_pesca` | INEGI — `series_inegi.csv` |
| INPP — con petróleo y servicios | `INPP_con_petroleo_servicios` | INEGI — `series_inegi.csv` |
| INPP — sin petróleo y servicios | `INPP_sin_petroleo_servicios` | INEGI — `series_inegi.csv` |
| INPP — energía eléctrica, agua y gas | `INPP_energia_electrica_agua_gas` | INEGI — `series_inegi.csv` |

---

### Bloque 6 — Salarios y costos laborales

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Remuneración de asalariados — total | `Remuneracion_asalariados_total` | INEGI — `series_inegi.csv` |
| Remuneraciones medias reales — total (EMIM) | `EMIM_remuneraciones_medias_reales` | INEGI — `series_inegi.csv` |

*Periodicidad:* el indicador BIE **724014** (remuneración total de asalariados) es de frecuencia **anual** en INEGI. En el archivo `series_inegi.csv` y en el panel puede figurar sobre **índice mensual** (`MS`) según cómo se haya alineado o interpolado al construir el panel; el inventario (`freq`) refleja la periodicidad **de la fuente**, no la rejilla del CSV.

---

### Bloque 7 — Tasas de interés

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Tasa de interés objetivo del Banco de México | `Tasa_objetivo` | Banxico — SIE — `series_banxico.csv` |
| CETES a 28 días (rendimiento en subasta) | `CETES_28_dias` | Banxico — SIE — `series_banxico.csv` |
| CETES a 91 días (rendimiento en subasta) | `CETES_91_dias` | Banxico — SIE — `series_banxico.csv` |
| CETES a 182 días (rendimiento en subasta) | `CETES_182_dias` | Banxico — SIE — `series_banxico.csv` |
| CETES a 364 días (rendimiento en subasta) | `CETES_364_dias` | Banxico — SIE — `series_banxico.csv` |
| TIIE a 28 días | `TIIE_28_dias` | Banxico — SIE — `series_banxico.csv` |
| Bono gubernamental a tasa fija — rendimiento 3 años (subasta) | `Mbono_tasa_fija_3y` | Banxico — SIE — `series_banxico.csv` |
| Bono gubernamental a tasa fija — rendimiento 5 años (subasta) | `Mbono_tasa_fija_5y` | Banxico — SIE — `series_banxico.csv` |
| Bono gubernamental a tasa fija — rendimiento 10 años (subasta) | `Mbono_tasa_fija_10y` | Banxico — SIE — `series_banxico.csv` |

---

### Bloque 8 — Dinero y crédito

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Agregado monetario M1 | `M1` | Banxico — SIE — `series_banxico.csv` |
| Agregado monetario M2 | `M2` | Banxico — SIE — `series_banxico.csv` |
| Agregado monetario M3 | `M3` | Banxico — SIE — `series_banxico.csv` |
| Agregado monetario M4 | `M4` | Banxico — SIE — `series_banxico.csv` |
| Crédito real al sector privado — cartera total | `Credito_real_sector_privado` | Banxico — SIE — `series_banxico.csv` |
| Cartera de crédito al consumo | `Credito_consumo` | Banxico — SIE — `series_banxico.csv` |
| Cartera de crédito a empresas (actividad empresarial) | `Credito_empresas_actividad_empresarial` | Banxico — SIE — `series_banxico.csv` |

---

### Bloque 9 — Tipo de cambio

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Tipo de cambio FIX (peso mexicano por dólar estadounidense) | `TC_FIX` | Banxico — SIE — `series_banxico.csv` |
| Expectativa de tipo de cambio al cierre del año (mediana; encuesta de especialistas) | `EE_TC_pesos_dolar_cierre_año_t_mediana` | Banxico — SIE — `series_banxico.csv` |

---

### Bloque 10 — Mercado bursátil

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Índice de Precios y Cotizaciones de la BMV (IPC; serie SIE) | `IPC_bolsa` | Banxico — SIE — `series_banxico.csv` |

---

### Bloque 11 — Expectativas y sentimiento

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Indicador de confianza del consumidor (ENCO) | `Confianza_consumidor` | INEGI — `series_inegi.csv` |
| Indicador global de opinión empresarial (IGOE / EMOE) | `Opinion_empresarial` | INEGI — `series_inegi.csv` |
| Expectativa de inflación general a 12 meses (mediana; encuesta de especialistas) | `EE_inflacion_general_prox12m_mediana` | Banxico — SIE — `series_banxico.csv` |
| Expectativa de variación del PIB real anual (mediana; año en curso) | `EE_PIB_real_anual_mediana_año_t` | Banxico — SIE — `series_banxico.csv` |

---

### Bloque 12 — Sector gobierno

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Ingreso total tributarios del Gobierno Federal (CG2; millones de pesos, flujos acumulados) | `Ingresos_tributarios_totales_GF_CG2_millones_pesos` | Banxico — SIE (cuadro CG2, sector 9) — `series_banxico.csv` |

> **Nota:** la serie corresponde al agregado **tributarios** del ingreso presupuestal en el SIE; no es estrictamente la suma exclusiva ISR+IVA+IEPS (ver comentarios en `Descarga_SeriesBANXICO.ipynb`).

---

### Bloque 13 — Indicadores financieros y externos

Series **presentes en el panel** que aquí se agrupan como indicadores financieros, de sector externo mexicano, flujos financieros e indicadores sintéticos de referencia. Siguen **sin** EMBIG, CDS ni otras primas de riesgo soberano — ver faltantes en `diagnostico_panel_mexico.md`.

| Nombre de la serie | Columna en panel | Fuente |
|---|---|---|
| Importaciones de bienes de capital | `Importaciones_bienes_capital` | INEGI — `series_inegi.csv` |
| Exportaciones manufactureras | `Exportaciones_manufactureras` | INEGI — `series_inegi.csv` |
| Remesas familiares deflactadas (reales, INPC) | `Remesas_reales_INPC` | Banxico — SIE — `series_banxico.csv` |
| Monto total de transferencias SPEI | `SPEI_monto_total_pesos` | Banxico — SIE — `series_banxico.csv` |
| Cuentas o contratos con tarjeta de crédito | `Cuentas_tarjeta_credito` | Banxico — SIE — `series_banxico.csv` |
| Indicador coincidente del SIC | `Coincidente_SIC` | INEGI — `series_inegi.csv` |
| Indicador adelantado del SIC | `Adelantado_SIC` | INEGI — `series_inegi.csv` |

*Periodicidad:* la serie **SF42525** (`Cuentas_tarjeta_credito`) es de frecuencia **trimestral** en el SIE; en el panel puede aparecer sobre **índice mensual** (`MS`) según la alineación o interpolación al armar `panel_series.csv`. El inventario marca la periodicidad **de la fuente**.

---

## Resumen por archivo de origen

| Origen | Nº de columnas en `panel_series.csv` | Archivo / flujo |
|--------|----------------------------------------|------------------|
| INEGI | 40 | `SeriesTiempo_INEGI/series_inegi.csv` |
| Banxico | 26 | `SeriesTiempo_BANXICO/series_banxico.csv` |

*El número de columnas por bloque en las tablas anteriores coincide con las 66 series listadas (40 + 26).*
