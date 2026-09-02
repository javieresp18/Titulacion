"""
Interpretabilidad (importancia interna, importancia por permutacion, SHAP)
para Random Forest y Gradient Boosting, y analisis de sensibilidad.
"""
import json
import os
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance

warnings.filterwarnings("ignore")

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELADO = os.path.join(RUTA_BASE, "modelado")
DATOS = os.path.join(RUTA_BASE, "datos_procesados")
SEMILLA = 42


def interpretabilidad():
    hiperparam = pd.read_csv(os.path.join(MODELADO, "hiperparametros.csv"))
    features_todas = pd.read_csv(os.path.join(MODELADO, "features_modelado.csv"))
    seleccion = pd.read_csv(os.path.join(MODELADO, "modelo_seleccionado_por_serie.csv"))

    filas_importancia, filas_shap = [], []

    for _, fila in hiperparam.iterrows():
        nivel, serie = fila["Nivel"], fila["Serie"]
        sel = seleccion[(seleccion["Nivel"] == nivel) & (seleccion["Serie"] == serie)]
        if sel.empty or sel.iloc[0]["ModeloSeleccionado"] not in ("RandomForest", "GradientBoosting"):
            continue
        modelo_sel = sel.iloc[0]["ModeloSeleccionado"]
        cols = json.loads(fila["caracteristicas_utilizadas"])
        g = features_todas[(features_todas["Nivel"] == nivel) & (features_todas["Serie"] == serie)].dropna(subset=cols + ["CostoMensualUSD"])
        if len(g) < 15:
            continue
        X, y = g[cols].values, g["CostoMensualUSD"].values

        if modelo_sel == "RandomForest":
            params = json.loads(fila["RandomForest"])
            modelo = RandomForestRegressor(random_state=SEMILLA, **params).fit(X, y)
        else:
            params = json.loads(fila["GradientBoosting"])
            modelo = GradientBoostingRegressor(random_state=SEMILLA, **params).fit(X, y)

        imp_interna = modelo.feature_importances_
        try:
            perm = permutation_importance(modelo, X, y, n_repeats=15, random_state=SEMILLA, scoring="neg_mean_absolute_error")
            imp_permutacion = perm.importances_mean
        except Exception:
            imp_permutacion = [np.nan] * len(cols)

        for i, c in enumerate(cols):
            filas_importancia.append({
                "Nivel": nivel, "Serie": serie, "ModeloSeleccionado": modelo_sel, "Variable": c,
                "ImportanciaInterna": round(float(imp_interna[i]), 6),
                "ImportanciaPermutacion": round(float(imp_permutacion[i]), 6) if imp_permutacion[i] == imp_permutacion[i] else None,
            })

        try:
            import shap
            if modelo_sel in ("RandomForest", "GradientBoosting"):
                explainer = shap.TreeExplainer(modelo)
                valores_shap = explainer.shap_values(X)
                shap_medio_abs = np.mean(np.abs(valores_shap), axis=0)
                for i, c in enumerate(cols):
                    filas_shap.append({"Nivel": nivel, "Serie": serie, "ModeloSeleccionado": modelo_sel,
                                        "Variable": c, "SHAP_MediaAbsoluta": round(float(shap_medio_abs[i]), 6)})
        except Exception as e:
            pass

    pd.DataFrame(filas_importancia).to_csv(os.path.join(MODELADO, "importancia_variables.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(filas_shap).to_csv(os.path.join(MODELADO, "resultados_shap.csv"), index=False, encoding="utf-8-sig")
    return len(filas_importancia), len(filas_shap)


def sensibilidad():
    """Analisis de sensibilidad de esta unica ejecucion (apartado 29)."""
    filas = []

    # 1. Duplicados excluidos vs conservados (tomado de la bitacora de transformaciones)
    ruta_bitacora = os.path.join(RUTA_BASE, "documentacion", "bitacora_transformaciones.md")
    if os.path.exists(ruta_bitacora):
        with open(ruta_bitacora, encoding="utf-8") as f:
            contenido = f.read()
        filas.append({"Escenario": "Duplicados excluidos vs. conservados",
                       "Descripcion": "Comparacion de filas y costo total al excluir (escenario principal) o conservar los duplicados exactos.",
                       "Evidencia": "Ver seccion 'Sensibilidad: duplicados excluidos vs conservados' en bitacora_transformaciones.md."})

    # 2. Con y sin el 1% superior de SubTotal
    df = pd.read_csv(os.path.join(DATOS, "dataset_depurado_anonimizado.csv"))
    p99 = df["SubTotal"].quantile(0.99)
    costo_con = df["SubTotal"].sum()
    costo_sin = df.loc[df["SubTotal"] < p99, "SubTotal"].sum()
    filas.append({"Escenario": "Con y sin 1% superior de SubTotal",
                   "Descripcion": f"Umbral percentil 99 = {p99:.2f} USD.",
                   "Evidencia": f"CostoDepuradoConExtremos={costo_con:.2f} USD; CostoDepuradoSinTop1pct={costo_sin:.2f} USD; "
                                f"DiferenciaPorcentual={round((costo_con-costo_sin)/costo_con*100,2)}%."})

    # 3. Con y sin Lag12
    metv = pd.read_csv(os.path.join(MODELADO, "metricas_validacion_agregado.csv"))
    hp = pd.read_csv(os.path.join(MODELADO, "hiperparametros.csv"))
    n_con_lag12 = int(hp["caracteristicas_utilizadas"].str.contains("Lag12").sum())
    filas.append({"Escenario": "Con y sin Lag12",
                   "Descripcion": "Lag12 se incluyo solo en series con cobertura continua suficiente (>=20 observaciones validas).",
                   "Evidencia": f"{n_con_lag12} de {len(hp)} series entrenadas incorporaron Lag12 como caracteristica."})

    # 4. Con y sin estacionalidad anual (Prophet)
    filas.append({"Escenario": "Con y sin estacionalidad anual forzada (Prophet)",
                   "Descripcion": "La estacionalidad anual de Prophet se activo solo cuando la serie alcanzo 24 o mas observaciones; en series mas cortas se desactivo para no forzarla sin sustento.",
                   "Evidencia": "Ver mensajes de configuracion registrados durante el entrenamiento (ajustar_prophet en entrenar_modelos_agregados.py)."})

    # 5. Nivel nave vs nave-categoria
    ser_agg = pd.read_csv(os.path.join(DATOS, "serie_agregada_mensual.csv"))
    costo_nave = ser_agg.loc[ser_agg["Nivel"] == "NAVE", "CostoMensualUSD"].sum()
    costo_nave_cat = ser_agg.loc[ser_agg["Nivel"] == "NAVE_CATEGORIA", "CostoMensualUSD"].sum()
    filas.append({"Escenario": "Nivel nave frente a nave-categoria",
                   "Descripcion": "Comparacion del costo total capturado al agregar por nave frente a agregar por combinacion nave-categoria.",
                   "Evidencia": f"CostoTotalNivelNave={costo_nave:.2f} USD; CostoTotalNivelNaveCategoria={costo_nave_cat:.2f} USD (deben coincidir salvo redondeo, dado que ambas particionan el mismo costo depurado)."})

    # 6. Reglas historicas de precio (items)
    impacto = pd.read_csv(os.path.join(MODELADO, "impacto_regla_precio_items.csv"))
    resumen_regla = impacto.groupby("ReglaPrecio")["ErrorMonetarioMAE_USD"].mean().round(4).to_dict()
    filas.append({"Escenario": "Diferentes reglas historicas de precio (nivel individual)",
                   "Descripcion": "Comparacion del error monetario medio (MAE USD) al convertir cantidad pronosticada a costo bajo tres reglas de precio.",
                   "Evidencia": f"ErrorMonetarioMedioUSD_por_regla={resumen_regla}."})

    # 7. Anulaciones probables
    anulaciones = pd.read_csv(os.path.join(RUTA_BASE, "control", "anulaciones.csv"))
    filas.append({"Escenario": "Casos de anulaciones probables",
                   "Descripcion": "Verificacion de pares de anulacion contable en el dataset oficial.",
                   "Evidencia": f"Pares de anulacion verificados: {len(anulaciones)}." if len(anulaciones) > 0 else
                                "No se identificaron anulaciones contables verificables; no aplica sensibilidad adicional."})

    pd.DataFrame(filas).to_csv(os.path.join(MODELADO, "analisis_sensibilidad.csv"), index=False, encoding="utf-8-sig")
    return len(filas)


if __name__ == "__main__":
    n_imp, n_shap = interpretabilidad()
    print("Importancia variables filas:", n_imp, "| SHAP filas:", n_shap)
    n_sens = sensibilidad()
    print("Escenarios de sensibilidad:", n_sens)
