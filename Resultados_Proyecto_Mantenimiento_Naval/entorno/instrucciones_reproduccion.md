# Instrucciones de reproduccion

## Requisitos

- Python 3.11 o superior.
- Instalar dependencias: `pip install -r entorno/requirements.txt`.
- Colocar `Dataset.xlsx` (fuente oficial de datos) en la raiz del paquete.

## Orden de ejecucion

Ejecutar desde la carpeta `codigo/`, en este orden (o mediante `python ejecutar_pipeline.py`, que los invoca automaticamente):

1. `python cargar_datos.py` — control del dataset y diccionario de datos.
2. `python depurar_datos.py` — auditoria de calidad, validacion monetaria, duplicados, anulaciones, categorias, depuracion, conciliacion y anonimizacion.
3. `python construir_series.py` — calendario mensual, series agregadas y de item, clasificacion ADI-CV2, ingenieria de caracteristicas.
4. `python entrenar_modelos_agregados.py` — validacion walk-forward y prueba final del nivel agregado (Random Forest, Gradient Boosting, suavizado exponencial, Prophet, naive).
5. `python entrenar_modelos_intermitentes.py` — Croston, SBA y bootstrap del nivel individual.
6. `python evaluar_modelos.py` — interpretabilidad (importancia de variables y SHAP) y analisis de sensibilidad.
7. `python generar_figuras.py` — figuras PNG para el articulo.
8. `python generar_documentacion.py` — matriz de trazabilidad, resumen ejecutivo e informe de resultados.
9. `python verificar_consistencia.py` — verificacion de referencias prohibidas antes de empaquetar.

## Reproducibilidad

- Todas las semillas aleatorias de los modelos de Machine Learning estan fijadas en `SEMILLA = 42`.
- El dataset de origen se identifica mediante su hash SHA-256, registrado en `control/control_ejecucion.json`.
- Un mismo archivo `Dataset.xlsx` produce siempre el mismo conjunto depurado y los mismos resultados de modelado.

## Notas de entorno

- `prophet` requiere `cmdstanpy` con un backend de Stan compilado; la primera ejecucion puede tardar mas por la compilacion inicial.
- Los archivos generados se ubican en `control/`, `datos_procesados/`, `modelado/`, `figuras/` y `documentacion/` segun corresponda.
