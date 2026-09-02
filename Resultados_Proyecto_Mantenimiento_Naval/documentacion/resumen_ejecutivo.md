# Resumen ejecutivo

Este resumen sintetiza la ejecucion del proyecto de prediccion de costos de mantenimiento naval mediante modelos de Machine Learning basados en series temporales de consumo de repuestos, desarrollada sobre Data-set.xlsx conforme a la metodologia establecida en Titulacion-Javier Espinoza.docx.

- Registros originales procesados: 21660.
- Filas depuradas conforme a los criterios de inclusion y exclusion: 18779.
- Costo bruto: 22447699.56 USD; costo depurado: 20954546.84 USD.
- Series agregadas elegibles evaluadas: 23.
- Distribucion de clasificacion ADI-CV2 de items: [{'Clasificacion': 'Intermitente', 'NumeroItems': 4104}, {'Clasificacion': 'Lumpy', 'NumeroItems': 446}].
- Modelo mas frecuentemente seleccionado en el nivel agregado (segun validacion walk-forward): Naive.
- MAE promedio en prueba final (2025), todas las series: 56457.83 USD.

Los detalles completos se encuentran en informe_resultados.md.
