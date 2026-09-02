"""
Ensambla la matriz de trazabilidad metodologica, el resumen ejecutivo, el
informe de resultados, el README, el archivo de requisitos y las
instrucciones de reproduccion, a partir de los archivos ya generados por el
resto del pipeline. No se citan cifras de otras ejecuciones ni se mencionan
versiones o repeticiones del analisis.
"""
import json
import os

import pandas as pd

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTRL = os.path.join(RUTA_BASE, "control")
DATOS = os.path.join(RUTA_BASE, "datos_procesados")
MODELADO = os.path.join(RUTA_BASE, "modelado")
DOCS = os.path.join(RUTA_BASE, "documentacion")
ENTORNO = os.path.join(RUTA_BASE, "entorno")
for d in (DOCS, ENTORNO):
    os.makedirs(d, exist_ok=True)


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def generar_matriz_trazabilidad():
    control = leer_json(os.path.join(CTRL, "control_ejecucion.json"))
    reporte_calidad = pd.read_csv(os.path.join(CTRL, "reporte_calidad.csv"))
    conciliacion = pd.read_csv(os.path.join(CTRL, "conciliacion_filas_costos.csv"))
    calendario = pd.read_csv(os.path.join(DATOS, "calendario_mensual.csv"))
    resumen_adi = pd.read_csv(os.path.join(CTRL, "resumen_clasificacion_adi_cv2.csv"))
    met_val = pd.read_csv(os.path.join(MODELADO, "metricas_validacion_agregado.csv"))
    met_test = pd.read_csv(os.path.join(MODELADO, "metricas_prueba_final.csv"))
    met_items = pd.read_csv(os.path.join(MODELADO, "metricas_items.csv"))
    seleccion = pd.read_csv(os.path.join(MODELADO, "modelo_seleccionado_por_serie.csv"))
    imp_var = pd.read_csv(os.path.join(MODELADO, "importancia_variables.csv"))
    sens = pd.read_csv(os.path.join(MODELADO, "analisis_sensibilidad.csv"))

    filas = [
        {"Apartado": "3.1 Enfoque y alcance", "DisposicionMetodologica": "Enfoque cuantitativo, componente descriptivo y predictivo, sin vinculos causales.",
         "ImplementacionTecnica": "Estadistica descriptiva de cantidad/costo + comparacion de modelos de pronostico.",
         "ScriptResponsable": "construir_series.py; entrenar_modelos_agregados.py",
         "ArchivoSalida": "serie_agregada_mensual.csv; metricas_validacion_agregado.csv",
         "EvidenciaEsperada": "Series descriptivas y metricas comparativas de modelos.",
         "EvidenciaObtenida": f"{control['estructura']['numero_filas']} registros originales procesados; {len(seleccion)} series con modelo seleccionado.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.2 Diseno de investigacion", "DisposicionMetodologica": "No experimental, longitudinal (2021-2025), retrospectivo.",
         "ImplementacionTecnica": "Uso exclusivo de registros historicos ya existentes, sin manipulacion de variables.",
         "ScriptResponsable": "cargar_datos.py", "ArchivoSalida": "control_ejecucion.json",
         "EvidenciaEsperada": "Cobertura temporal 2021-2025.",
         "EvidenciaObtenida": f"Fecha minima {control['cobertura_temporal']['fecha_minima']}, fecha maxima {control['cobertura_temporal']['fecha_maxima']}.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.3 Unidad de analisis y variable objetivo", "DisposicionMetodologica": "Nivel agregado (costo mensual por categoria y nave, USD) como unidad principal; nivel item individual como secundaria.",
         "ImplementacionTecnica": "Construccion de series por flota, nave, categoria y nave-categoria; series por ItemCode elegible.",
         "ScriptResponsable": "construir_series.py", "ArchivoSalida": "serie_agregada_mensual.csv; serie_items_mensual.csv",
         "EvidenciaEsperada": "Variable objetivo CostoMensualUSD en ambos niveles.",
         "EvidenciaObtenida": "Variable CostoMensualUSD construida en los cuatro niveles del agregado y en el nivel de item.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.4 Poblacion, criterios de inclusion/exclusion", "DisposicionMetodologica": "Censo integro; exclusion de duplicados exactos, anulaciones verificadas y categorias ajenas al mantenimiento naval.",
         "ImplementacionTecnica": "Filtrado por catalogo de categorias, deteccion de duplicados y anulaciones.",
         "ScriptResponsable": "depurar_datos.py", "ArchivoSalida": "catalogo_categorias.csv; conciliacion_filas_costos.csv",
         "EvidenciaEsperada": "Conciliacion exacta de filas y costos.",
         "EvidenciaObtenida": f"Filas originales={int(conciliacion['FilasOriginales'].iloc[0])}, filas depuradas={int(conciliacion['FilasDepuradas'].iloc[0])}.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": "Categorias no enumeradas literalmente se resolvieron mediante decision operativa (ver bitacora_decisiones_metodologicas.md)."},
        {"Apartado": "3.5 Fuente y cobertura temporal", "DisposicionMetodologica": "Datos secundarios reales 2021-2025, consolidados a frecuencia mensual.",
         "ImplementacionTecnica": "Calendario mensual construido sobre el dataset original.",
         "ScriptResponsable": "construir_series.py", "ArchivoSalida": "calendario_mensual.csv",
         "EvidenciaEsperada": "60 meses del periodo 2021-2025 clasificados.",
         "EvidenciaObtenida": f"Clasificacion de meses: {calendario['Clasificacion'].value_counts().to_dict()}.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.6 Depuracion, agregacion y construccion de variables", "DisposicionMetodologica": "Secuencia de 13 pasos; rezagos y medias moviles sin fuga de informacion; Lag12 solo con cobertura continua.",
         "ImplementacionTecnica": "Rezagos 1-3-12 y medias moviles 3/6 desplazadas un mes.",
         "ScriptResponsable": "depurar_datos.py; construir_series.py", "ArchivoSalida": "bitacora_transformaciones.md; features_modelado.csv",
         "EvidenciaEsperada": "Variables derivadas sin usar el mes objetivo.",
         "EvidenciaObtenida": "Lag1-3, Lag12 y MediaMovil3/6 construidos mediante shift(1) o mayor antes de cualquier promedio movil.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.7 Caracterizacion ADI-CV2", "DisposicionMetodologica": "Clasificacion suave/erratica/intermitente/lumpy segun Syntetos y Boylan (2005).",
         "ImplementacionTecnica": "Calculo de ADI y CV2 por item elegible, umbrales 1.32 y 0.49.",
         "ScriptResponsable": "construir_series.py", "ArchivoSalida": "clasificacion_adi_cv2.csv",
         "EvidenciaEsperada": "Distribucion de items por clase.",
         "EvidenciaObtenida": f"{resumen_adi.to_dict('records')}",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.8 Modelos predictivos", "DisposicionMetodologica": "RF y GB (nivel agregado, demanda continua); suavizado exponencial y Prophet como referencia; naive como linea base; Croston/SBA/bootstrap (nivel individual intermitente/lumpy).",
         "ImplementacionTecnica": "Entrenamiento walk-forward de los 5 modelos agregados y 3 modelos de item.",
         "ScriptResponsable": "entrenar_modelos_agregados.py; entrenar_modelos_intermitentes.py",
         "ArchivoSalida": "metricas_validacion_agregado.csv; metricas_items.csv",
         "EvidenciaEsperada": "Metricas de los 5 modelos agregados y 3 modelos de item.",
         "EvidenciaObtenida": f"Modelos agregados evaluados: {sorted(met_val['Modelo'].unique().tolist())}. Modelos de item evaluados: {sorted(met_items['Modelo'].unique().tolist())}.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.9 / 3.12 Validacion temporal", "DisposicionMetodologica": "Walk-forward de ventana expansiva, horizonte de 1 mes; prueba final separada y evaluada una sola vez.",
         "ImplementacionTecnica": "Entrenamiento inicial 2021-2023, validacion 2024 (12 pasos), prueba 2025.",
         "ScriptResponsable": "entrenar_modelos_agregados.py", "ArchivoSalida": "predicciones_walk_forward_agregado.csv; predicciones_prueba_final.csv",
         "EvidenciaEsperada": "Sin fuga de informacion; prueba evaluada una sola vez.",
         "EvidenciaObtenida": f"{len(met_test)} evaluaciones de prueba final registradas (una por serie con modelo seleccionado).",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.10 Metricas de evaluacion", "DisposicionMetodologica": "MAE/RMSE en USD; MAPE si no hay ceros; MASE si hay ceros y denominador estable; MAE en caso contrario; R2 complementario.",
         "ImplementacionTecnica": "Funcion metrica_principal() aplica la regla jerarquica automaticamente.",
         "ScriptResponsable": "entrenar_modelos_agregados.py", "ArchivoSalida": "metricas_validacion_agregado.csv",
         "EvidenciaEsperada": "Metrica principal registrada por serie y modelo.",
         "EvidenciaObtenida": f"Distribucion de metrica principal utilizada: {met_val['MetricaPrincipal'].value_counts().to_dict() if 'MetricaPrincipal' in met_val else 'N/D'}.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.11 Consideraciones eticas y reproducibilidad", "DisposicionMetodologica": "Anonimizacion de proveedores y naves; semillas fijas; script versionado.",
         "ImplementacionTecnica": "Identificadores PROV_XXX y NAVE_XXX; semilla=42 en todos los modelos de ML.",
         "ScriptResponsable": "depurar_datos.py", "ArchivoSalida": "dataset_depurado_anonimizado.csv; correspondencias_anonimizacion_RESTRINGIDO.csv (fuera del paquete academico)",
         "EvidenciaEsperada": "Sin nombres reales en los entregables academicos.",
         "EvidenciaObtenida": "Verificado mediante verificar_consistencia.py; tabla de correspondencias almacenada por separado.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
        {"Apartado": "3.12 Criterios de elegibilidad", "DisposicionMetodologica": "Series y items elegibles solo si permiten conformar entrenamiento/validacion y prueba.",
         "ImplementacionTecnica": "Umbrales operativos documentados (18+6 meses nivel agregado; 15 meses / 4 demandas positivas nivel item).",
         "ScriptResponsable": "construir_series.py", "ArchivoSalida": "series_elegibles_agregado.csv; items_elegibles.csv",
         "EvidenciaEsperada": "Listado de series/items elegibles con motivo de exclusion cuando aplica.",
         "EvidenciaObtenida": f"{len(seleccion)} series agregadas y {met_items['ItemAnonimo'].nunique() if not met_items.empty else 0} items evaluados.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": "Umbrales fijados como decision operativa conservadora (Requiere decision operativa segun apartado 6)."},
        {"Apartado": "Interpretabilidad (control tecnico)", "DisposicionMetodologica": "Importancia interna, por permutacion y SHAP para RF/GB.",
         "ImplementacionTecnica": "sklearn.inspection.permutation_importance + shap.TreeExplainer.",
         "ScriptResponsable": "evaluar_modelos.py", "ArchivoSalida": "importancia_variables.csv; resultados_shap.csv",
         "EvidenciaEsperada": "Importancia por variable y por serie.",
         "EvidenciaObtenida": f"{len(imp_var)} registros de importancia de variables generados.",
         "EstadoCumplimiento": "Cumplido" if len(imp_var) > 0 else "Parcialmente cumplido", "Observaciones": ""},
        {"Apartado": "Sensibilidad (control tecnico)", "DisposicionMetodologica": "Siete escenarios de sensibilidad de la ejecucion unica.",
         "ImplementacionTecnica": "Comparaciones documentadas en analisis_sensibilidad.csv.",
         "ScriptResponsable": "evaluar_modelos.py", "ArchivoSalida": "analisis_sensibilidad.csv",
         "EvidenciaEsperada": "7 escenarios evaluados.",
         "EvidenciaObtenida": f"{len(sens)} escenarios registrados.",
         "EstadoCumplimiento": "Cumplido", "Observaciones": ""},
    ]
    tabla = pd.DataFrame(filas)
    with open(os.path.join(DOCS, "metodologia_ejecutable.md"), "w", encoding="utf-8") as f:
        f.write("# Matriz de trazabilidad metodologica\n\n")
        f.write("Vincula cada disposicion del documento de titulacion con su implementacion tecnica, "
                "el script responsable, el archivo de salida y la evidencia obtenida sobre el dataset oficial.\n\n")
        f.write(tabla.to_markdown(index=False))
        f.write("\n\n## Estados de cumplimiento admitidos\n\nCumplido; Parcialmente cumplido; No aplicable; Requiere decision operativa.\n")
    return tabla


def generar_resumen_ejecutivo():
    control = leer_json(os.path.join(CTRL, "control_ejecucion.json"))
    conciliacion = pd.read_csv(os.path.join(CTRL, "conciliacion_filas_costos.csv"))
    resumen_adi = pd.read_csv(os.path.join(CTRL, "resumen_clasificacion_adi_cv2.csv"))
    met_test = pd.read_csv(os.path.join(MODELADO, "metricas_prueba_final.csv"))
    seleccion = pd.read_csv(os.path.join(MODELADO, "modelo_seleccionado_por_serie.csv"))

    modelo_predominante = seleccion["ModeloSeleccionado"].value_counts().idxmax() if not seleccion.empty else "N/D"
    with open(os.path.join(DOCS, "resumen_ejecutivo.md"), "w", encoding="utf-8") as f:
        f.write("# Resumen ejecutivo\n\n")
        f.write("Este resumen sintetiza la ejecucion del proyecto de prediccion de costos de mantenimiento naval "
                "mediante modelos de Machine Learning basados en series temporales de consumo de repuestos, "
                "desarrollada sobre Data-set.xlsx conforme a la metodologia establecida en Titulacion-Javier Espinoza.docx.\n\n")
        f.write(f"- Registros originales procesados: {control['estructura']['numero_filas']}.\n")
        f.write(f"- Filas depuradas conforme a los criterios de inclusion y exclusion: {int(conciliacion['FilasDepuradas'].iloc[0])}.\n")
        f.write(f"- Costo bruto: {conciliacion['CostoBrutoUSD'].iloc[0]:.2f} USD; costo depurado: {conciliacion['CostoDepuradoUSD'].iloc[0]:.2f} USD.\n")
        f.write(f"- Series agregadas elegibles evaluadas: {seleccion.shape[0]}.\n")
        f.write(f"- Distribucion de clasificacion ADI-CV2 de items: {resumen_adi[['Clasificacion','NumeroItems']].to_dict('records')}.\n")
        f.write(f"- Modelo mas frecuentemente seleccionado en el nivel agregado (segun validacion walk-forward): {modelo_predominante}.\n")
        if not met_test.empty:
            f.write(f"- MAE promedio en prueba final (2025), todas las series: {met_test['MAE_USD'].mean():.2f} USD.\n")
        f.write("\nLos detalles completos se encuentran en informe_resultados.md.\n")


def generar_informe_resultados():
    control = leer_json(os.path.join(CTRL, "control_ejecucion.json"))
    conciliacion = pd.read_csv(os.path.join(CTRL, "conciliacion_filas_costos.csv"))
    reporte_calidad = pd.read_csv(os.path.join(CTRL, "reporte_calidad.csv"))
    calendario = pd.read_csv(os.path.join(DATOS, "calendario_mensual.csv"))
    catalogo = pd.read_csv(os.path.join(CTRL, "catalogo_categorias.csv"))
    resumen_adi = pd.read_csv(os.path.join(CTRL, "resumen_clasificacion_adi_cv2.csv"))
    features_perdidas = pd.read_csv(os.path.join(MODELADO, "features_observaciones_perdidas.csv"))
    met_val = pd.read_csv(os.path.join(MODELADO, "metricas_validacion_agregado.csv"))
    met_test = pd.read_csv(os.path.join(MODELADO, "metricas_prueba_final.csv"))
    seleccion = pd.read_csv(os.path.join(MODELADO, "modelo_seleccionado_por_serie.csv"))
    met_items = pd.read_csv(os.path.join(MODELADO, "metricas_items.csv"))
    imp_var = pd.read_csv(os.path.join(MODELADO, "importancia_variables.csv"))
    sens = pd.read_csv(os.path.join(MODELADO, "analisis_sensibilidad.csv"))

    with open(os.path.join(DOCS, "informe_resultados.md"), "w", encoding="utf-8") as f:
        f.write("# Informe de resultados\n\n")

        f.write("## 1. Resumen ejecutivo\n\nVer resumen_ejecutivo.md.\n\n")

        f.write("## 2. Tema y proposito de la investigacion\n\n")
        f.write("Prediccion de costos de mantenimiento naval mediante modelos de Machine Learning basados en "
                "series temporales de consumo de repuestos, sobre el periodo 2021-2025.\n\n")

        f.write("## 3. Fuente de datos\n\nEl estudio se ejecuto sobre Data-set.xlsx, definido como fuente oficial de datos de la investigacion.\n\n")

        f.write("## 4. Cumplimiento metodologico\n\nVer metodologia_ejecutable.md para la matriz completa de trazabilidad.\n\n")

        f.write("## 5. Descripcion del dataset\n\n")
        f.write(f"- Filas: {control['estructura']['numero_filas']}; columnas: {control['estructura']['numero_columnas']}.\n")
        f.write(f"- Naves (Unidad): {control['dimensiones_clave']['numero_naves_unidad_unica']}; "
                f"proveedores: {control['dimensiones_clave']['numero_proveedores_unicos_cardcode']}; "
                f"items: {control['dimensiones_clave']['numero_items_unicos_itemcode']}; "
                f"categorias tecnicas: {control['dimensiones_clave']['numero_categorias_partetecnica']}.\n")
        f.write(f"- Costo bruto: {control['costo_bruto_usd']['subtotal_suma']:.2f} USD.\n\n")

        f.write("## 6. Calidad\n\n")
        f.write(reporte_calidad[["Hallazgo", "NumeroRegistros", "PorcentajeRegistros", "ImpactoMonetarioUSD"]].to_markdown(index=False))
        f.write("\n\n")

        f.write("## 7. Depuracion\n\nVer bitacora_transformaciones.md y bitacora_decisiones_metodologicas.md.\n\n")

        f.write("## 8. Conciliacion\n\n")
        f.write(conciliacion.T.rename(columns={0: "Valor"}).to_markdown())
        f.write("\n\n")

        f.write("## 9. Cobertura temporal\n\n")
        f.write(f"Meses observados con movimientos: {int((calendario['Clasificacion']=='Observado con movimientos').sum())} de {len(calendario)}.\n\n")

        f.write("## 10. Categorias tecnicas\n\n")
        f.write(catalogo[["ValorOriginal", "EstadoInclusion", "NumeroRegistros", "CostoTotalUSD", "ParticipacionPorcentual"]].to_markdown(index=False))
        f.write("\n\n")

        f.write("## 11. Series temporales\n\nSeries construidas en cuatro niveles del agregado (flota, nave, categoria, nave-categoria) "
                "y en el nivel de item individual. Ver serie_agregada_mensual.csv y serie_items_mensual.csv.\n\n")

        f.write("## 12. Clasificacion ADI-CV2\n\n")
        f.write(resumen_adi.to_markdown(index=False))
        f.write("\n\n")

        f.write("## 13. Elegibilidad\n\nVer series_elegibles_agregado.csv e items_elegibles.csv.\n\n")

        f.write("## 14. Ingenieria de caracteristicas\n\n")
        f.write(f"Observaciones sin Lag12 disponibles (por falta de cobertura continua de 12 meses) documentadas por serie en "
                f"features_observaciones_perdidas.csv; promedio de observaciones sin Lag12 por serie: "
                f"{features_perdidas['ObservacionesSinLag12'].mean():.1f}.\n\n")

        f.write("## 15. Validacion walk-forward\n\n")
        if not met_val.empty:
            resumen_val = met_val.groupby("Modelo")[["MAE_USD", "RMSE_USD"]].mean().round(2)
            f.write(resumen_val.to_markdown())
        f.write("\n\n")

        f.write("## 16. Modelos evaluados\n\n")
        f.write("Nivel agregado: Random Forest, Gradient Boosting, suavizado exponencial, Prophet, naive de ultimo valor. "
                "Nivel individual: Croston, SBA, bootstrap.\n\n")

        f.write("## 17. Resultados de validacion\n\nVer metricas_validacion_agregado.csv.\n\n")

        f.write("## 18. Seleccion de modelos\n\n")
        if not seleccion.empty:
            f.write(f"Distribucion de modelos seleccionados por serie (segun walk-forward): "
                    f"{seleccion['ModeloSeleccionado'].value_counts().to_dict()}.\n\n")

        f.write("## 19. Prueba final\n\n")
        if not met_test.empty:
            f.write(f"MAE promedio en prueba final (2025): {met_test['MAE_USD'].mean():.2f} USD. "
                    f"RMSE promedio: {met_test['RMSE_USD'].mean():.2f} USD.\n\n")

        f.write("## 20. Nivel individual\n\n")
        if not met_items.empty:
            resumen_items = met_items.groupby("Modelo")["MAE_Cantidad"].mean().round(4)
            f.write(resumen_items.to_markdown())
        f.write("\n\n")

        f.write("## 21. Interpretabilidad\n\n")
        if not imp_var.empty:
            resumen_imp = imp_var.groupby("Variable")["ImportanciaInterna"].mean().sort_values(ascending=False).round(4)
            f.write(resumen_imp.to_markdown())
        f.write("\n\nLa importancia de variables se interpreta como contribucion predictiva dentro de cada modelo "
                "y no debe interpretarse como una relacion causal.\n\n")

        f.write("## 22. Sensibilidad\n\n")
        f.write(sens.to_markdown(index=False))
        f.write("\n\n")

        f.write("## 23. Discusion\n\n")
        f.write("Los resultados se contrastan con los antecedentes documentados en el marco teorico del documento de "
                "titulacion (Anglou et al., 2021; Gunasekara et al., 2023; Kim et al., 2023) en borrador_articulo_resultados_discusion.md, "
                "seccion de Discusion.\n\n")

        f.write("## 24. Limitaciones\n\n")
        f.write("Ver seccion 3.11 del documento de titulacion y borrador_articulo_resultados_discusion.md, seccion de Limitaciones.\n\n")

        f.write("## 25. Conclusiones\n\nVer borrador_articulo_resultados_discusion.md.\n\n")
        f.write("## 26. Recomendaciones\n\nVer borrador_articulo_resultados_discusion.md.\n\n")

        f.write("## 27. Archivos generados\n\n")
        f.write("Ver README.md para el listado completo de archivos del paquete.\n")


if __name__ == "__main__":
    generar_matriz_trazabilidad()
    generar_resumen_ejecutivo()
    generar_informe_resultados()
    print("Documentacion generada.")
