# Informe de resultados

## 1. Resumen ejecutivo

Ver resumen_ejecutivo.md.

## 2. Tema y proposito de la investigacion

Prediccion de costos de mantenimiento naval mediante modelos de Machine Learning basados en series temporales de consumo de repuestos, sobre el periodo 2021-2025.

## 3. Fuente de datos

El estudio se ejecuto sobre Data-set.xlsx, definido como fuente oficial de datos de la investigacion.

## 4. Cumplimiento metodologico

Ver metodologia_ejecutable.md para la matriz completa de trazabilidad.

## 5. Descripcion del dataset

- Filas: 21660; columnas: 14.
- Naves (Unidad): 14; proveedores: 528; items: 5291; categorias tecnicas: 10.
- Costo bruto: 22447699.56 USD.

## 6. Calidad

| Hallazgo                                                        |   NumeroRegistros |   PorcentajeRegistros |   ImpactoMonetarioUSD |
|:----------------------------------------------------------------|------------------:|----------------------:|----------------------:|
| Fechas invalidas/nulas                                          |                 0 |                0      |           0           |
| Cantidades negativas                                            |                 0 |                0      |           0           |
| Cantidades iguales a cero                                       |                 0 |                0      |           0           |
| Precios negativos                                               |                 0 |                0      |           0           |
| Precios iguales a cero                                          |                 4 |                0.0185 |        1516.62        |
| Descuentos negativos                                            |                81 |                0.374  |       98081.1         |
| Descuentos inconsistentes                                       |             13836 |               63.8781 |           1.27039e+07 |
| Subtotales negativos                                            |                 0 |                0      |           0           |
| Subtotales iguales a cero                                       |                 0 |                0      |           0           |
| Valores de error de Excel (#N/A, #DIV/0!, etc.)                 |                 0 |                0      |           0           |
| Codigos sin descripcion                                         |                 0 |                0      |           0           |
| Codigos asociados con descripciones diferentes                  |              3332 |               15.3832 |           2.29987e+06 |
| Naves sin identificar                                           |                 0 |                0      |           0           |
| Proveedores sin identificar                                     |                 0 |                0      |           0           |
| Valores extremos (percentil 99 de SubTotal, solo documentacion) |               217 |                1.0018 |           9.60769e+06 |

## 7. Depuracion

Ver bitacora_transformaciones.md y bitacora_decisiones_metodologicas.md.

## 8. Conciliacion

|                              |            Valor |
|:-----------------------------|-----------------:|
| FilasOriginales              |  21660           |
| DuplicadosExcluidos          |    250           |
| AnulacionesVerificadas       |      0           |
| CategoriasExcluidas          |   2631           |
| OtrasExclusionesJustificadas |      0           |
| FilasDepuradas               |  18779           |
| CostoBrutoUSD                |      2.24477e+07 |
| CostoDuplicadosExcluidosUSD  | 572378           |
| EfectoAnulacionesUSD         |      0           |
| CostoCategoriasExcluidasUSD  | 920774           |
| EfectoOtrasExclusionesUSD    |      0           |
| CostoDepuradoUSD             |      2.09545e+07 |
| CostoDepuradoCalculadoUSD    |      2.09545e+07 |

## 9. Cobertura temporal

Meses observados con movimientos: 60 de 60.

## 10. Categorias tecnicas

| ValorOriginal              | EstadoInclusion   |   NumeroRegistros |    CostoTotalUSD |   ParticipacionPorcentual |
|:---------------------------|:------------------|------------------:|-----------------:|--------------------------:|
| ACEITE                     | INCLUIDA          |               490 | 617984           |                    2.753  |
| FERRETERIA                 | INCLUIDA          |              8591 |      1.93508e+06 |                    8.6204 |
| FILTROS                    | INCLUIDA          |               473 | 198638           |                    0.8849 |
| GRASAS                     | INCLUIDA          |                12 |   1609.85        |                    0.0072 |
| MATERIALES DE LIMPIEZA     | EXCLUIDA          |               977 |  77576.8         |                    0.3456 |
| PINTURAS                   | EXCLUIDA          |              1660 | 843470           |                    3.7575 |
| QUIMICOS                   | INCLUIDA          |               542 | 178989           |                    0.7974 |
| REPUESTOS ELECTRICOS       | INCLUIDA          |               215 | 192426           |                    0.8572 |
| REPUESTOS MECANICOS        | INCLUIDA          |              3462 |      4.89337e+06 |                   21.799  |
| SERVICIOS DE MANTENIMIENTO | INCLUIDA          |              5238 |      1.35086e+07 |                   60.1779 |

## 11. Series temporales

Series construidas en cuatro niveles del agregado (flota, nave, categoria, nave-categoria) y en el nivel de item individual. Ver serie_agregada_mensual.csv y serie_items_mensual.csv.

## 12. Clasificacion ADI-CV2

| Clasificacion   |   NumeroItems |   CostoTotalUSD |   ParticipacionPorcentual |   UmbralADI |   UmbralCV2 |
|:----------------|--------------:|----------------:|--------------------------:|------------:|------------:|
| Intermitente    |          4104 |     1.8172e+07  |                     93.24 |        1.32 |        0.49 |
| Lumpy           |           446 |     1.31697e+06 |                      6.76 |        1.32 |        0.49 |

## 13. Elegibilidad

Ver series_elegibles_agregado.csv e items_elegibles.csv.

## 14. Ingenieria de caracteristicas

Observaciones sin Lag12 disponibles (por falta de cobertura continua de 12 meses) documentadas por serie en features_observaciones_perdidas.csv; promedio de observaciones sin Lag12 por serie: 12.0.

## 15. Validacion walk-forward

| Modelo               |   MAE_USD |   RMSE_USD |
|:---------------------|----------:|-----------:|
| GradientBoosting     |   73684.7 |   102780   |
| Naive                |   58004.3 |    87907.4 |
| Prophet              |  116155   |   151958   |
| RandomForest         |   73648.4 |    95308.3 |
| SuavizadoExponencial |   79405.1 |   107357   |

## 16. Modelos evaluados

Nivel agregado: Random Forest, Gradient Boosting, suavizado exponencial, Prophet, naive de ultimo valor. Nivel individual: Croston, SBA, bootstrap.

## 17. Resultados de validacion

Ver metricas_validacion_agregado.csv.

## 18. Seleccion de modelos

Distribucion de modelos seleccionados por serie (segun walk-forward): {'Naive': 19, 'Prophet': 2, 'GradientBoosting': 1, 'SuavizadoExponencial': 1}.

## 19. Prueba final

MAE promedio en prueba final (2025): 56457.83 USD. RMSE promedio: 82187.96 USD.

## 20. Nivel individual

| Modelo    |   MAE_Cantidad |
|:----------|---------------:|
| Bootstrap |        11.1648 |
| Croston   |        14.7346 |
| SBA       |        14.1132 |

## 21. Interpretabilidad

| Variable       |   ImportanciaInterna |
|:---------------|---------------------:|
| Lag2           |               0.1878 |
| Lag1           |               0.1852 |
| IndiceTemporal |               0.1588 |
| Lag3           |               0.1406 |
| MediaMovil6    |               0.1208 |
| MediaMovil3    |               0.0784 |
| Lag12          |               0.0752 |
| MesNumerico    |               0.0497 |
| Trimestre      |               0.0035 |

La importancia de variables se interpreta como contribucion predictiva dentro de cada modelo y no debe interpretarse como una relacion causal.

## 22. Sensibilidad

| Escenario                                                 | Descripcion                                                                                                                                                        | Evidencia                                                                                                                                                               |
|:----------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Duplicados excluidos vs. conservados                      | Comparacion de filas y costo total al excluir (escenario principal) o conservar los duplicados exactos.                                                            | Ver seccion 'Sensibilidad: duplicados excluidos vs conservados' en bitacora_transformaciones.md.                                                                        |
| Con y sin 1% superior de SubTotal                         | Umbral percentil 99 = 13090.05 USD.                                                                                                                                | CostoDepuradoConExtremos=20954546.84 USD; CostoDepuradoSinTop1pct=12098324.58 USD; DiferenciaPorcentual=42.26%.                                                         |
| Con y sin Lag12                                           | Lag12 se incluyo solo en series con cobertura continua suficiente (>=20 observaciones validas).                                                                    | 23 de 23 series entrenadas incorporaron Lag12 como caracteristica.                                                                                                      |
| Con y sin estacionalidad anual forzada (Prophet)          | La estacionalidad anual de Prophet se activo solo cuando la serie alcanzo 24 o mas observaciones; en series mas cortas se desactivo para no forzarla sin sustento. | Ver mensajes de configuracion registrados durante el entrenamiento (ajustar_prophet en entrenar_modelos_agregados.py).                                                  |
| Nivel nave frente a nave-categoria                        | Comparacion del costo total capturado al agregar por nave frente a agregar por combinacion nave-categoria.                                                         | CostoTotalNivelNave=20954546.84 USD; CostoTotalNivelNaveCategoria=20954546.84 USD (deben coincidir salvo redondeo, dado que ambas particionan el mismo costo depurado). |
| Diferentes reglas historicas de precio (nivel individual) | Comparacion del error monetario medio (MAE USD) al convertir cantidad pronosticada a costo bajo tres reglas de precio.                                             | ErrorMonetarioMedioUSD_por_regla={'promedio_historico': 5424.0568, 'promedio_movil_historico': 9545.7982, 'ultimo_precio_conocido': 13797.0579}.                        |
| Casos de anulaciones probables                            | Verificacion de pares de anulacion contable en el dataset oficial.                                                                                                 | No se identificaron anulaciones contables verificables; no aplica sensibilidad adicional.                                                                               |

## 23. Discusion

Los resultados se contrastan con los antecedentes documentados en el marco teorico del documento de titulacion (Anglou et al., 2021; Gunasekara et al., 2023; Kim et al., 2023) en borrador_articulo_resultados_discusion.md, seccion de Discusion.

## 24. Limitaciones

Ver seccion 3.11 del documento de titulacion y borrador_articulo_resultados_discusion.md, seccion de Limitaciones.

## 25. Conclusiones

Ver borrador_articulo_resultados_discusion.md.

## 26. Recomendaciones

Ver borrador_articulo_resultados_discusion.md.

## 27. Archivos generados

Ver README.md para el listado completo de archivos del paquete.
