"""
Modelos del nivel de item individual para demanda intermitente o lumpy:
Croston, Syntetos-Boylan Approximation (SBA) y bootstrap (Willemain et al., 2004).

Se pronostica primero Quantity; la conversion a costo usa unicamente
informacion de precios disponible antes del periodo objetivo (ultimo precio
conocido, promedio historico disponible, promedio movil historico). Nunca se
usa el precio real futuro.
"""
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RUTA_BASE, "datos_procesados")
MODELADO = os.path.join(RUTA_BASE, "modelado")
SEMILLA = 42
ALPHA_CROSTON = 0.1  # decision operativa: constante de suavizado fija (ver bitacora_decisiones_metodologicas.md)

PERIODO_INICIO = pd.Period("2021-01", freq="M")
PERIODO_FIN = pd.Period("2025-12", freq="M")


def croston(serie, alpha=ALPHA_CROSTON, correccion_sba=False):
    """Devuelve el pronostico Croston (o SBA) de un paso adelante dado el
    historico completo 'serie' (array de cantidades, incluye ceros)."""
    serie = np.asarray(serie, dtype=float)
    idx_no_cero = np.where(serie > 0)[0]
    if len(idx_no_cero) == 0:
        return 0.0
    z = serie[idx_no_cero[0]]  # nivel de demanda
    p = idx_no_cero[0] + 1 if idx_no_cero[0] > 0 else 1  # intervalo entre demandas
    q = 1
    for t in range(idx_no_cero[0] + 1, len(serie)):
        if serie[t] > 0:
            z = alpha * serie[t] + (1 - alpha) * z
            p = alpha * q + (1 - alpha) * p
            q = 1
        else:
            q += 1
    pronostico = z / p if p > 0 else 0.0
    if correccion_sba:
        pronostico *= (1 - alpha / 2)
    return float(pronostico)


def bootstrap_willemain(serie, n_boot=200, horizonte=1, semilla=SEMILLA):
    """Bootstrap de dos estados (Willemain et al., 2004), version simplificada:
    remuestrea la ocurrencia (cero/no cero) segun la proporcion historica y
    remuestrea la magnitud entre los valores positivos historicos, aplicando
    un jitter uniforme leve. Devuelve la media de las trayectorias simuladas
    como pronostico puntual de un paso adelante."""
    rng = np.random.default_rng(semilla)
    serie = np.asarray(serie, dtype=float)
    positivos = serie[serie > 0]
    prob_no_cero = float((serie > 0).mean()) if len(serie) else 0.0
    if len(positivos) == 0 or prob_no_cero == 0:
        return 0.0
    simulaciones = []
    for _ in range(n_boot):
        ocurre = rng.random() < prob_no_cero
        if not ocurre:
            simulaciones.append(0.0)
        else:
            base = rng.choice(positivos)
            jitter = rng.uniform(-0.15, 0.15) * base
            simulaciones.append(max(base + jitter, 0.0))
    return float(np.mean(simulaciones))


def mae(y_true, y_pred):
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def mase(y_true, y_pred, y_train_hist):
    y_train_hist = np.asarray(y_train_hist, dtype=float)
    if len(y_train_hist) < 2:
        return None
    denom = np.mean(np.abs(np.diff(y_train_hist)))
    if not np.isfinite(denom) or denom < 1e-6:
        return None
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))) / denom)


def regla_precio(precios_hist, cantidades_hist, regla):
    precios_validos = precios_hist[~np.isnan(precios_hist)]
    if len(precios_validos) == 0:
        return np.nan
    if regla == "ultimo_precio_conocido":
        return float(precios_validos[-1])
    if regla == "promedio_historico":
        return float(np.mean(precios_validos))
    if regla == "promedio_movil_historico":
        ventana = precios_validos[-3:] if len(precios_validos) >= 3 else precios_validos
        return float(np.mean(ventana))
    return np.nan


def ejecutar():
    serie_items = pd.read_csv(os.path.join(DATOS, "serie_items_mensual.csv"))
    clasif = pd.read_csv(os.path.join(DATOS, "clasificacion_adi_cv2.csv"))
    items_elegibles = clasif.loc[clasif["Elegible"], "ItemAnonimo"].tolist()

    meses_calendario = pd.period_range(PERIODO_INICIO, PERIODO_FIN, freq="M")

    predicciones, metricas, impacto_precio = [], [], []

    for item in items_elegibles:
        g = serie_items[serie_items["ItemAnonimo"] == item].copy()
        g["PeriodoMes"] = pd.PeriodIndex(g["Mes"], freq="M")
        g = g.set_index("PeriodoMes").reindex(meses_calendario)
        cantidad = g["CantidadMensual"].fillna(0).clip(lower=0).values
        precio = g["PrecioUnitarioPonderado"].values

        n_test = 6  # ultimos 6 meses reservados como prueba (decision operativa: ver bitacora)
        n_total = len(cantidad)
        if n_total - n_test < 12:
            continue
        idx_test_start = n_total - n_test

        for modelo, func in [("Croston", lambda s: croston(s, correccion_sba=False)),
                              ("SBA", lambda s: croston(s, correccion_sba=True)),
                              ("Bootstrap", lambda s: bootstrap_willemain(s))]:
            preds_cant = []
            for t in range(idx_test_start, n_total):
                hist = cantidad[:t]
                preds_cant.append(func(hist))
            reales_cant = cantidad[idx_test_start:n_total]

            mae_cant = mae(reales_cant, preds_cant)
            mase_cant = mase(reales_cant, preds_cant, cantidad[:idx_test_start])
            metrica_cant_nombre = "MASE" if mase_cant is not None else "MAE"
            metrica_cant_valor = mase_cant if mase_cant is not None else mae_cant

            for regla in ["ultimo_precio_conocido", "promedio_historico", "promedio_movil_historico"]:
                preds_costo, reales_costo = [], []
                for k, t in enumerate(range(idx_test_start, n_total)):
                    precios_hist = precio[:t]
                    p_hat = regla_precio(precios_hist, cantidad[:t], regla)
                    costo_pred = preds_cant[k] * p_hat if not np.isnan(p_hat) else np.nan
                    preds_costo.append(costo_pred)
                    reales_costo.append(g["CostoMensualUSD"].fillna(0).values[t])
                    predicciones.append({
                        "ItemAnonimo": item, "Modelo": modelo, "ReglaPrecio": regla,
                        "Mes": str(meses_calendario[t]), "CantidadReal": float(reales_cant[k]),
                        "CantidadPredicha": float(preds_cant[k]), "CostoRealUSD": float(reales_costo[-1]),
                        "CostoPredichoUSD": float(costo_pred) if not np.isnan(costo_pred) else None,
                    })
                validos = [(a, b) for a, b in zip(reales_costo, preds_costo) if not np.isnan(b)]
                error_monetario = mae([a for a, b in validos], [b for a, b in validos]) if validos else None
                impacto_precio.append({
                    "ItemAnonimo": item, "Modelo": modelo, "ReglaPrecio": regla,
                    "ErrorMonetarioMAE_USD": round(error_monetario, 4) if error_monetario is not None else None,
                })

            metricas.append({
                "ItemAnonimo": item, "Modelo": modelo,
                "MetricaCantidadPrincipal": metrica_cant_nombre,
                "ValorMetricaCantidad": round(metrica_cant_valor, 4) if metrica_cant_valor is not None else None,
                "MAE_Cantidad": round(mae_cant, 4),
            })

    df_pred = pd.DataFrame(predicciones)
    df_pred.to_csv(os.path.join(MODELADO, "predicciones_items.csv"), index=False, encoding="utf-8-sig")
    df_met = pd.DataFrame(metricas)
    df_met.to_csv(os.path.join(MODELADO, "metricas_items.csv"), index=False, encoding="utf-8-sig")
    df_impacto = pd.DataFrame(impacto_precio)
    df_impacto.to_csv(os.path.join(MODELADO, "impacto_regla_precio_items.csv"), index=False, encoding="utf-8-sig")

    return {"n_items": len(items_elegibles), "n_predicciones": len(df_pred)}


if __name__ == "__main__":
    print(ejecutar())
