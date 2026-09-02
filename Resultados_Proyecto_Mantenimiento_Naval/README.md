# Prediccion de costos de mantenimiento naval

Este paquete contiene la ejecucion reproducible del proyecto de investigacion "Prediccion de costos de mantenimiento naval mediante modelos de Machine Learning basados en series temporales de consumo de repuestos".

El analisis utiliza Data-set.xlsx como fuente oficial de datos y sigue la introduccion, el marco teorico y la metodologia establecidos en Titulacion-Javier Espinoza.docx. El procedimiento comprende la auditoria y depuracion de los registros, la anonimizacion, la construccion de series temporales mensuales, la caracterizacion ADI-CV2, la evaluacion de modelos mediante validacion walk-forward y la prueba final sobre un periodo cronologicamente separado.

## Objetivo

Desarrollar y evaluar modelos de Machine Learning basados en series temporales para predecir los costos de mantenimiento naval asociados al consumo de repuestos, a partir de registros historicos del periodo 2021-2025.

## Archivos oficiales utilizados

- `Dataset.xlsx` — fuente oficial de datos de la investigacion (no incluido en este paquete por contener informacion identificable de proveedores y naves; ver anonimizacion).
- Documento de titulacion — fuente oficial del contexto academico y la metodologia.

## Metodologia aplicada

Enfoque cuantitativo, no experimental, longitudinal y retrospectivo, con dos niveles de analisis: agregado (costo mensual por categoria tecnica y nave) e individual (item elegible). Validacion cronologica de ventana expansiva (walk-forward) con prueba final separada. Metricas MAE, RMSE, MAPE, MASE y R2 complementario segun el apartado 3.10 del documento de titulacion. Ver `documentacion/metodologia_ejecutable.md` para la matriz de trazabilidad completa.

## Estructura del paquete

```
Resultados_Proyecto_Mantenimiento_Naval/
├── README.md
├── control/                  Control del dataset, calidad y conciliacion
├── codigo/                   Scripts reproducibles del pipeline
├── datos_procesados/         Dataset depurado y series construidas
├── modelado/                 Predicciones, metricas e interpretabilidad
├── figuras/                  16 figuras PNG para el articulo
├── documentacion/            Matriz de trazabilidad, bitacoras, informes y borrador
└── entorno/                  Requisitos y guia de reproduccion
```

## Requisitos

Ver `entorno/requirements.txt`. Python 3.11 o superior.

## Orden de ejecucion

Ver `entorno/instrucciones_reproduccion.md`. En sintesis: `python codigo/ejecutar_pipeline.py` desde la raiz del paquete, con `Dataset.xlsx` presente.

## Resultados principales

- Registros originales: 21 660; registros depurados: 18 779; costo bruto: 22 447 699,56 USD; costo depurado: 20 954 546,84 USD.
- 23 series del nivel agregado y 64 items del nivel individual cumplieron los criterios de elegibilidad y fueron modelados.
- En la validacion walk-forward, el naive de ultimo valor obtuvo el menor error promedio (MAE 58 004,33 USD), seguido de Random Forest (73 648,40 USD) y Gradient Boosting (73 684,66 USD); Prophet obtuvo el mayor error (116 154,71 USD).
- En la prueba final (2025), el MAE promedio entre series fue de 56 457,83 USD.
- Todos los items elegibles del nivel individual se clasificaron como demanda intermitente o lumpy; el bootstrap obtuvo el menor error de cantidad promedio (MAE 11,16 unidades) frente a Croston (14,73) y SBA (14,11).

Ver `documentacion/informe_resultados.md` y `documentacion/borrador_articulo_resultados_discusion.md` para el detalle completo.

## Limitaciones

Ver la seccion 3.11 del documento de titulacion y la seccion de limitaciones de `documentacion/borrador_articulo_resultados_discusion.md`.

## Instrucciones de reproduccion

Ver `entorno/instrucciones_reproduccion.md`.
