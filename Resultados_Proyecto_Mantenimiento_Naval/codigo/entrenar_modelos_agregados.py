"""
Entrenamiento y validacion walk-forward de los modelos del nivel agregado:
Random Forest, Gradient Boosting (Machine Learning), suavizado exponencial y
Prophet (metodos de referencia) y naive de ultimo valor (linea base tecnica).

Validacion temporal (apartados 3.9 y 3.12):
- Entrenamiento inicial: 2021-01 a 2023-12 (36 meses).
- Validacion walk-forward de ventana expansiva: 2024-01 a 2024-12 (12 pasos,
  horizonte de un mes).
- Prueba final, completamente separada y evaluada una sola vez: 2025.
"""
import json
import os
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor

warnings.filterwarnings("ignore")

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELADO = os.path.join(RUTA_BASE, "modelado")
DATOS = os.path.join(RUTA_BASE, "datos_procesados")
os.makedirs(MODELADO, exist_ok=True)

SEMILLA = 42
FEATURES_BASE = ["MesNumerico", "Trimestre", "IndiceTemporal", "Lag1", "Lag2", "Lag3", "MediaMovil3", "MediaMovil6"]
FEATURE_LAG12 = "Lag12"

CORTE_TRAIN_INICIAL_FIN = "2023-12"
CORTE_VALIDACION_FIN = "2024-12"
CORTE_TEST_INICIO = "2025-01"


def cargar_features():
    f = pd.read_csv(os.path.join(MODELADO, "features_modelado.csv"))
    f["PeriodoMes"] = pd.PeriodIndex(f["Mes"], freq="M")
    return f


def mae(y_true, y_pred):
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    if np.any(y_true == 0):
        return None
    return float(np.mean(np.abs((y_true - np.asarray(y_pred)) / y_true)) * 100)


def mase(y_true, y_pred, y_train_hist):
    y_train_hist = np.asarray(y_train_hist, dtype=float)
    if len(y_train_hist) < 2:
        return None
    denom = np.mean(np.abs(np.diff(y_train_hist)))
    if not np.isfinite(denom) or denom < 1e-6:
        return None
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))) / denom)


def metrica_principal(y_true_hist_train, y_true, y_pred):
    """Aplica la regla del apartado 3.10 para el nivel agregado."""
    m_mape = mape(y_true, y_pred)
    if m_mape is not None:
        return "MAPE", m_mape
    m_mase = mase(y_true, y_pred, y_true_hist_train)
    if m_mase is not None:
        return "MASE", m_mase
    return "MAE", mae(y_true, y_pred)


def preparar_serie(features, nivel, serie, usar_lag12):
    g = features[(features["Nivel"] == nivel) & (features["Serie"] == serie)].sort_values("PeriodoMes").reset_index(drop=True)
    cols = FEATURES_BASE + ([FEATURE_LAG12] if usar_lag12 else [])
    g_valid = g.dropna(subset=cols + ["CostoMensualUSD"]).reset_index(drop=True)
    return g, g_valid, cols


GRID_RF = [{"n_estimators": 100, "max_depth": 5}, {"n_estimators": 200, "max_depth": None}, {"n_estimators": 300, "max_depth": 8}]
GRID_GB = [{"n_estimators": 100, "learning_rate": 0.1, "max_depth": 2},
           {"n_estimators": 200, "learning_rate": 0.05, "max_depth": 3},
           {"n_estimators": 150, "learning_rate": 0.1, "max_depth": 3}]


def ajustar_expsmoothing(y_hist):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    y_hist = np.asarray(y_hist, dtype=float)
    y_hist = np.where(y_hist <= 0, 1e-3, y_hist)
    try:
        if len(y_hist) >= 24:
            modelo = ExponentialSmoothing(y_hist, trend="add", seasonal="add", seasonal_periods=12, initialization_method="estimated")
        else:
            modelo = ExponentialSmoothing(y_hist, trend="add", seasonal=None, initialization_method="estimated")
        ajuste = modelo.fit(optimized=True)
        return float(ajuste.forecast(1)[0])
    except Exception:
        return float(y_hist[-1])


def ajustar_prophet(fechas_hist, y_hist):
    from prophet import Prophet
    df_p = pd.DataFrame({"ds": pd.PeriodIndex(fechas_hist, freq="M").to_timestamp(), "y": y_hist})
    usar_estacionalidad_anual = len(df_p) >= 24
    modelo = Prophet(yearly_seasonality=usar_estacionalidad_anual, weekly_seasonality=False, daily_seasonality=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import logging
        logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
        modelo.fit(df_p)
    futuro = modelo.make_future_dataframe(periods=1, freq="MS")
    pred = modelo.predict(futuro)
    return float(pred["yhat"].iloc[-1])


def entrenar_serie(nivel, serie, g_valid, cols):
    resultado = {"predicciones_val": [], "metricas_val": {}, "hiperparametros": {}, "tiempos": {}}
    meses = g_valid["PeriodoMes"]
    idx_ini_val = g_valid.index[meses.astype(str) == "2024-01"]
    idx_fin_val = g_valid.index[meses.astype(str) == "2024-12"]
    idx_ini_test = g_valid.index[meses.astype(str) == "2025-01"]
    if len(idx_ini_val) == 0 or len(idx_fin_val) == 0:
        return None
    i_val_start, i_val_end = idx_ini_val[0], idx_fin_val[0]
    i_test_start = idx_ini_test[0] if len(idx_ini_test) else None

    X = g_valid[cols].values
    y = g_valid["CostoMensualUSD"].values
    y_dates = g_valid["PeriodoMes"].values

    if i_val_start < 6:
        return None  # ventana inicial insuficiente

    # --- Walk-forward RF y GB: grid acotado evaluado en cada paso, se agrega el error medio por config ---
    preds_wf = {"RandomForest": [], "GradientBoosting": [], "SuavizadoExponencial": [], "Prophet": [], "Naive": []}
    reales_wf = []
    fechas_wf = []
    errores_grid_rf = {i: [] for i in range(len(GRID_RF))}
    errores_grid_gb = {i: [] for i in range(len(GRID_GB))}

    t0 = time.time()
    for t in range(i_val_start, i_val_end + 1):
        X_train, y_train = X[:t], y[:t]
        x_t, y_t = X[t], y[t]
        reales_wf.append(y_t)
        fechas_wf.append(str(y_dates[t]))

        for i, params in enumerate(GRID_RF):
            m = RandomForestRegressor(random_state=SEMILLA, **params)
            m.fit(X_train, y_train)
            p = m.predict(x_t.reshape(1, -1))[0]
            errores_grid_rf[i].append(abs(p - y_t))
            if i == 0:
                preds_wf["RandomForest"].append(p)  # placeholder, se recalcula tras elegir grid

        for i, params in enumerate(GRID_GB):
            m = GradientBoostingRegressor(random_state=SEMILLA, **params)
            m.fit(X_train, y_train)
            p = m.predict(x_t.reshape(1, -1))[0]
            errores_grid_gb[i].append(abs(p - y_t))
            if i == 0:
                preds_wf["GradientBoosting"].append(p)

        # Naive: ultimo valor observado
        preds_wf["Naive"].append(y_train[-1])

        # Suavizado exponencial y Prophet: usan la serie real (no rezagada)
        y_hist_real = g_valid["CostoMensualUSD"].values[:t]
        fechas_hist_real = g_valid["PeriodoMes"].values[:t]
        preds_wf["SuavizadoExponencial"].append(ajustar_expsmoothing(y_hist_real))
        try:
            preds_wf["Prophet"].append(ajustar_prophet(fechas_hist_real, y_hist_real))
        except Exception:
            preds_wf["Prophet"].append(float(y_hist_real[-1]))

    tiempo_val = time.time() - t0

    mejor_rf_idx = int(np.argmin([np.mean(v) for v in errores_grid_rf.values()]))
    mejor_gb_idx = int(np.argmin([np.mean(v) for v in errores_grid_gb.values()]))

    # Recalcular predicciones RF y GB del walk-forward con la mejor config (reproducible)
    preds_rf_final, preds_gb_final = [], []
    for t in range(i_val_start, i_val_end + 1):
        X_train, y_train = X[:t], y[:t]
        x_t = X[t]
        m_rf = RandomForestRegressor(random_state=SEMILLA, **GRID_RF[mejor_rf_idx]).fit(X_train, y_train)
        m_gb = GradientBoostingRegressor(random_state=SEMILLA, **GRID_GB[mejor_gb_idx]).fit(X_train, y_train)
        preds_rf_final.append(m_rf.predict(x_t.reshape(1, -1))[0])
        preds_gb_final.append(m_gb.predict(x_t.reshape(1, -1))[0])
    preds_wf["RandomForest"] = preds_rf_final
    preds_wf["GradientBoosting"] = preds_gb_final

    y_hist_train_inicial = y[:i_val_start]
    metricas_val = {}
    for modelo, preds in preds_wf.items():
        nombre_metrica, valor = metrica_principal(y_hist_train_inicial, reales_wf, preds)
        metricas_val[modelo] = {
            "MetricaPrincipal": nombre_metrica, "ValorMetricaPrincipal": round(valor, 4) if valor is not None else None,
            "MAE_USD": round(mae(reales_wf, preds), 2), "RMSE_USD": round(rmse(reales_wf, preds), 2),
            "R2_complementario": round(1 - np.sum((np.array(reales_wf) - np.array(preds)) ** 2) /
                                        max(np.sum((np.array(reales_wf) - np.mean(reales_wf)) ** 2), 1e-9), 4),
        }

    predicciones_val_rows = []
    for i, fecha in enumerate(fechas_wf):
        row = {"Nivel": nivel, "Serie": serie, "Mes": fecha, "Real": reales_wf[i]}
        for modelo in preds_wf:
            row[f"Pred_{modelo}"] = preds_wf[modelo][i]
        predicciones_val_rows.append(row)

    hiperparametros = {
        "RandomForest": GRID_RF[mejor_rf_idx], "GradientBoosting": GRID_GB[mejor_gb_idx],
        "grid_evaluado_RandomForest": GRID_RF, "grid_evaluado_GradientBoosting": GRID_GB,
        "semilla": SEMILLA, "tiempo_entrenamiento_validacion_seg": round(tiempo_val, 3),
        "numero_observaciones_entrenamiento_inicial": int(i_val_start),
        "caracteristicas_utilizadas": cols,
    }

    # Seleccion del modelo por serie: menor valor en la metrica principal walk-forward
    metrica_ref = {k: v["ValorMetricaPrincipal"] for k, v in metricas_val.items() if v["ValorMetricaPrincipal"] is not None}
    modelo_seleccionado = min(metrica_ref, key=metrica_ref.get) if metrica_ref else "Naive"

    # --- Prueba final: reentrena el modelo seleccionado con train+val completo, evalua 1 vez en 2025 ---
    resultado_test = None
    if i_test_start is not None:
        X_trainval, y_trainval = X[:i_test_start], y[:i_test_start]
        X_test, y_test = X[i_test_start:], y[i_test_start:]
        fechas_test = g_valid["PeriodoMes"].values[i_test_start:]
        t0 = time.time()
        if modelo_seleccionado == "RandomForest":
            m = RandomForestRegressor(random_state=SEMILLA, **GRID_RF[mejor_rf_idx]).fit(X_trainval, y_trainval)
            preds_test = m.predict(X_test)
        elif modelo_seleccionado == "GradientBoosting":
            m = GradientBoostingRegressor(random_state=SEMILLA, **GRID_GB[mejor_gb_idx]).fit(X_trainval, y_trainval)
            preds_test = m.predict(X_test)
        elif modelo_seleccionado == "SuavizadoExponencial":
            preds_test = []
            y_real_trainval = list(g_valid["CostoMensualUSD"].values[:i_test_start])
            for k in range(len(y_test)):
                preds_test.append(ajustar_expsmoothing(y_real_trainval))
                y_real_trainval.append(y_test[k])
        elif modelo_seleccionado == "Prophet":
            preds_test = []
            y_real_trainval = list(g_valid["CostoMensualUSD"].values[:i_test_start])
            fechas_acum = list(g_valid["PeriodoMes"].values[:i_test_start])
            for k in range(len(y_test)):
                try:
                    preds_test.append(ajustar_prophet(fechas_acum, y_real_trainval))
                except Exception:
                    preds_test.append(y_real_trainval[-1])
                y_real_trainval.append(y_test[k]); fechas_acum.append(fechas_test[k])
        else:
            preds_test = [y_trainval[-1]] + list(y_test[:-1])
        tiempo_test = time.time() - t0
        nombre_m, valor_m = metrica_principal(y_hist_train_inicial, y_test, preds_test)
        resultado_test = {
            "modelo": modelo_seleccionado,
            "predicciones": [{"Nivel": nivel, "Serie": serie, "Mes": str(fechas_test[k]), "Real": float(y_test[k]), "Prediccion": float(preds_test[k])} for k in range(len(y_test))],
            "metricas": {
                "MetricaPrincipal": nombre_m, "ValorMetricaPrincipal": round(valor_m, 4) if valor_m is not None else None,
                "MAE_USD": round(mae(y_test, preds_test), 2), "RMSE_USD": round(rmse(y_test, preds_test), 2),
                "R2_complementario": round(1 - np.sum((y_test - np.array(preds_test)) ** 2) / max(np.sum((y_test - np.mean(y_test)) ** 2), 1e-9), 4),
                "tiempo_prediccion_seg": round(tiempo_test, 3),
            },
        }

    return {
        "predicciones_val": predicciones_val_rows, "metricas_val": metricas_val,
        "hiperparametros": hiperparametros, "modelo_seleccionado": modelo_seleccionado,
        "resultado_test": resultado_test, "cols": cols,
    }


def ejecutar(series_muestra=None):
    features = cargar_features()
    elegibilidad = pd.read_csv(os.path.join(DATOS, "series_elegibles_agregado.csv"))
    elegibles = elegibilidad[elegibilidad["Elegible"]]

    todas_pred_val, todas_metricas_val, todos_hiperparam = [], [], []
    todas_pred_test, todas_metricas_test = [], []
    resumen_modelos = []

    lista_series = list(elegibles[["Nivel", "Serie"]].itertuples(index=False, name=None))
    if series_muestra:
        lista_series = lista_series[:series_muestra]

    for nivel, serie in lista_series:
        _, g_valid, cols_con_lag12 = preparar_serie(features, nivel, serie, usar_lag12=True)
        usar_lag12 = len(g_valid) >= 20
        cols = cols_con_lag12 if usar_lag12 else FEATURES_BASE
        _, g_valid, cols = preparar_serie(features, nivel, serie, usar_lag12=usar_lag12)
        if len(g_valid) < 20:
            continue
        res = entrenar_serie(nivel, serie, g_valid, cols)
        if res is None:
            continue
        todas_pred_val.extend(res["predicciones_val"])
        for modelo, m in res["metricas_val"].items():
            todas_metricas_val.append({"Nivel": nivel, "Serie": serie, "Modelo": modelo, **m})
        todos_hiperparam.append({"Nivel": nivel, "Serie": serie, **{k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in res["hiperparametros"].items()}})
        resumen_modelos.append({"Nivel": nivel, "Serie": serie, "ModeloSeleccionado": res["modelo_seleccionado"]})
        if res["resultado_test"]:
            todas_pred_test.extend(res["resultado_test"]["predicciones"])
            todas_metricas_test.append({"Nivel": nivel, "Serie": serie, "Modelo": res["modelo_seleccionado"], **res["resultado_test"]["metricas"]})

    pd.DataFrame(todas_pred_val).to_csv(os.path.join(MODELADO, "predicciones_walk_forward_agregado.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(todas_metricas_val).to_csv(os.path.join(MODELADO, "metricas_validacion_agregado.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(todos_hiperparam).to_csv(os.path.join(MODELADO, "hiperparametros.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(todas_pred_test).to_csv(os.path.join(MODELADO, "predicciones_prueba_final.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(todas_metricas_test).to_csv(os.path.join(MODELADO, "metricas_prueba_final.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(resumen_modelos).to_csv(os.path.join(MODELADO, "modelo_seleccionado_por_serie.csv"), index=False, encoding="utf-8-sig")

    return {
        "n_series_entrenadas": len(resumen_modelos),
        "seleccion": pd.DataFrame(resumen_modelos)["ModeloSeleccionado"].value_counts().to_dict() if resumen_modelos else {},
    }


if __name__ == "__main__":
    t0 = time.time()
    resumen = ejecutar()
    print(resumen)
    print("Tiempo total (s):", round(time.time() - t0, 1))
