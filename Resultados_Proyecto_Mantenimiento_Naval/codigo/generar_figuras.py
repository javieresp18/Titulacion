"""
Generacion de figuras para el articulo (PNG, en espanol, resolucion apta
para publicacion). No se incluyen nombres reales ni referencias a versiones.
"""
import json
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 300, "font.size": 10})

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RUTA_BASE, "datos_procesados")
CTRL = os.path.join(RUTA_BASE, "control")
MODELADO = os.path.join(RUTA_BASE, "modelado")
FIG = os.path.join(RUTA_BASE, "figuras")
os.makedirs(FIG, exist_ok=True)


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, nombre), bbox_inches="tight")
    plt.close(fig)


def fig01_flujo_metodologico():
    etapas = ["Carga y\ncontrol", "Auditoria de\ncalidad", "Depuracion y\nconciliacion",
              "Anonimizacion", "Construccion\nde series", "Clasificacion\nADI-CV2",
              "Ingenieria de\ncaracteristicas", "Validacion\nwalk-forward",
              "Entrenamiento\nde modelos", "Prueba final", "Interpretabilidad\ny sensibilidad"]
    fig, ax = plt.subplots(figsize=(13, 3.2))
    x = np.arange(len(etapas))
    for i, e in enumerate(etapas):
        ax.add_patch(plt.Rectangle((i - 0.42, -0.3), 0.84, 0.6, fill=True, color="#2c5f8a", alpha=0.85))
        ax.text(i, 0, e, ha="center", va="center", color="white", fontsize=8, wrap=True)
        if i < len(etapas) - 1:
            ax.annotate("", xy=(i + 0.58, 0), xytext=(i + 0.42, 0),
                        arrowprops=dict(arrowstyle="->", color="black"))
    ax.set_xlim(-0.6, len(etapas) - 0.4)
    ax.set_ylim(-0.6, 0.6)
    ax.axis("off")
    ax.set_title("Flujo metodologico del pipeline reproducible")
    guardar(fig, "01_flujo_metodologico.png")


def fig02_distribucion_registros_por_anio():
    with open(os.path.join(CTRL, "control_ejecucion.json"), encoding="utf-8") as f:
        control = json.load(f)
    reg = control["cobertura_temporal"]["registros_por_anio"]
    anios = sorted(reg.keys())
    valores = [reg[a] for a in anios]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(anios, valores, color="#2c5f8a")
    for i, v in enumerate(valores):
        ax.text(i, v + max(valores) * 0.01, str(v), ha="center", fontsize=9)
    ax.set_xlabel("Anio")
    ax.set_ylabel("Numero de registros")
    ax.set_title("Distribucion de registros por anio (dataset oficial)")
    guardar(fig, "02_distribucion_registros_anio.png")


def fig03_cobertura_mensual():
    cal = pd.read_csv(os.path.join(DATOS, "calendario_mensual.csv"))
    fig, ax = plt.subplots(figsize=(13, 4))
    colores = cal["Clasificacion"].map({
        "Observado con movimientos": "#2c5f8a", "Observado sin movimientos": "#f0a500",
        "Sin cobertura verificable": "#c0392b",
    }).fillna("#999999")
    ax.bar(cal["Mes"], cal["NumeroRegistros"], color=colores)
    ax.set_xticks(range(0, len(cal), 3))
    ax.set_xticklabels(cal["Mes"][::3], rotation=90, fontsize=7)
    ax.set_ylabel("Numero de registros")
    ax.set_title("Cobertura mensual del periodo 2021-2025 (dataset oficial)")
    guardar(fig, "03_cobertura_mensual.png")


def fig04_costo_mensual_total():
    ser = pd.read_csv(os.path.join(DATOS, "serie_agregada_mensual.csv"))
    flota = ser[ser["Nivel"] == "FLOTA"].sort_values("Mes")
    fig, ax = plt.subplots(figsize=(13, 4.5))
    ax.plot(flota["Mes"], flota["CostoMensualUSD"], marker="o", color="#2c5f8a", linewidth=1.5, markersize=3)
    ax.set_xticks(range(0, len(flota), 3))
    ax.set_xticklabels(flota["Mes"].iloc[::3], rotation=90, fontsize=7)
    ax.set_ylabel("Costo mensual (USD)")
    ax.set_title("Costo mensual total de la flota (dataset depurado)")
    guardar(fig, "04_costo_mensual_total.png")


def fig05_costo_mensual_por_nave():
    ser = pd.read_csv(os.path.join(DATOS, "serie_agregada_mensual.csv"))
    naves = ser[ser["Nivel"] == "NAVE"]
    top_naves = naves.groupby("Serie")["CostoMensualUSD"].sum().nlargest(8).index
    fig, ax = plt.subplots(figsize=(13, 5))
    for nave in top_naves:
        g = naves[naves["Serie"] == nave].sort_values("Mes")
        ax.plot(g["Mes"], g["CostoMensualUSD"], label=nave, linewidth=1)
    ax.set_xticks(range(0, ser["Mes"].nunique(), 6))
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    ax.set_ylabel("Costo mensual (USD)")
    ax.set_title("Costo mensual por nave anonimizada (8 principales por costo total)")
    ax.legend(fontsize=7, ncol=2)
    guardar(fig, "05_costo_mensual_por_nave.png")


def fig06_costo_mensual_por_categoria():
    ser = pd.read_csv(os.path.join(DATOS, "serie_agregada_mensual.csv"))
    cats = ser[ser["Nivel"] == "CATEGORIA"]
    top_cat = cats.groupby("Serie")["CostoMensualUSD"].sum().nlargest(8).index
    fig, ax = plt.subplots(figsize=(13, 5))
    for cat in top_cat:
        g = cats[cats["Serie"] == cat].sort_values("Mes")
        ax.plot(g["Mes"], g["CostoMensualUSD"], label=cat, linewidth=1)
    ax.set_xticks(range(0, ser["Mes"].nunique(), 6))
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    ax.set_ylabel("Costo mensual (USD)")
    ax.set_title("Costo mensual por categoria tecnica (8 principales por costo total)")
    ax.legend(fontsize=7, ncol=2)
    guardar(fig, "06_costo_mensual_por_categoria.png")


def fig07_distribucion_subtotal():
    df = pd.read_csv(os.path.join(DATOS, "dataset_depurado_anonimizado.csv"))
    st = df["SubTotal"].clip(lower=0.01)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(np.log10(st), bins=50, color="#2c5f8a")
    ax.set_xlabel("log10(SubTotal en USD)")
    ax.set_ylabel("Frecuencia")
    ax.set_title("Distribucion de SubTotal (escala logaritmica, dataset depurado)")
    guardar(fig, "07_distribucion_subtotal.png")


def fig08_pareto_costos():
    df = pd.read_csv(os.path.join(DATOS, "dataset_depurado_anonimizado.csv"))
    por_cat = df.groupby("ParteTecnica")["SubTotal"].sum().sort_values(ascending=False)
    acumulado = por_cat.cumsum() / por_cat.sum() * 100
    fig, ax1 = plt.subplots(figsize=(11, 5))
    ax1.bar(range(len(por_cat)), por_cat.values, color="#2c5f8a")
    ax1.set_xticks(range(len(por_cat)))
    ax1.set_xticklabels(por_cat.index, rotation=75, ha="right", fontsize=7)
    ax1.set_ylabel("Costo total (USD)")
    ax2 = ax1.twinx()
    ax2.plot(range(len(por_cat)), acumulado.values, color="#c0392b", marker="o", markersize=3)
    ax2.set_ylabel("Porcentaje acumulado (%)")
    ax2.axhline(80, color="gray", linestyle="--", linewidth=0.8)
    ax1.set_title("Pareto de costos por categoria tecnica (dataset depurado)")
    guardar(fig, "08_pareto_costos.png")


def fig09_clasificacion_adi_cv2():
    clasif = pd.read_csv(os.path.join(DATOS, "clasificacion_adi_cv2.csv")).dropna(subset=["ADI", "CV2"])
    fig, ax = plt.subplots(figsize=(7.5, 6))
    colores = {"Suave": "#2c5f8a", "Erratica": "#f0a500", "Intermitente": "#27ae60", "Lumpy": "#c0392b", "No clasificable": "#999999"}
    for clase, g in clasif.groupby("Clasificacion"):
        ax.scatter(g["ADI"], g["CV2"], s=14, alpha=0.6, label=f"{clase} (n={len(g)})", color=colores.get(clase, "black"))
    ax.axvline(1.32, color="black", linestyle="--", linewidth=0.8)
    ax.axhline(0.49, color="black", linestyle="--", linewidth=0.8)
    ax.set_xlabel("ADI (intervalo promedio entre demandas)")
    ax.set_ylabel("CV2 (coeficiente de variacion al cuadrado)")
    ax.set_title("Clasificacion ADI-CV2 de items elegibles (umbrales de Syntetos y Boylan, 2005)")
    ax.legend(fontsize=8)
    guardar(fig, "09_clasificacion_adi_cv2.png")


def fig10_esquema_walk_forward():
    fig, ax = plt.subplots(figsize=(12, 3.5))
    total_meses = 60
    train_ini = 36
    val_fin = 48
    ax.barh(0, train_ini, left=0, color="#2c5f8a", label="Entrenamiento inicial (2021-2023)")
    ax.barh(0, val_fin - train_ini, left=train_ini, color="#f0a500", label="Validacion walk-forward (2024, ventana expansiva)")
    ax.barh(0, total_meses - val_fin, left=val_fin, color="#c0392b", label="Prueba final (2025, evaluacion unica)")
    for i in range(train_ini, val_fin):
        ax.annotate("", xy=(i + 1, 0.45), xytext=(0, 0.45), arrowprops=dict(arrowstyle="->", color="gray", lw=0.5))
    ax.set_yticks([])
    ax.set_xlabel("Mes (indice 0-59, periodo 2021-2025)")
    ax.set_title("Esquema de validacion walk-forward de ventana expansiva")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3, fontsize=8)
    guardar(fig, "10_esquema_walk_forward.png")


def fig11_metricas_validacion_por_modelo():
    met = pd.read_csv(os.path.join(MODELADO, "metricas_validacion_agregado.csv"))
    resumen = met.groupby("Modelo")["MAE_USD"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(resumen.index, resumen.values, color="#2c5f8a")
    ax.set_xlabel("MAE promedio de validacion walk-forward (USD)")
    ax.set_title("Metricas de validacion walk-forward por modelo (promedio entre series)")
    guardar(fig, "11_metricas_validacion_por_modelo.png")


def fig12_real_vs_prediccion():
    pred = pd.read_csv(os.path.join(MODELADO, "predicciones_prueba_final.csv"))
    if pred.empty:
        return
    serie_top = pred.groupby(["Nivel", "Serie"])["Real"].sum().idxmax()
    g = pred[(pred["Nivel"] == serie_top[0]) & (pred["Serie"] == serie_top[1])].sort_values("Mes")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(g["Mes"], g["Real"], marker="o", label="Real", color="#2c5f8a")
    ax.plot(g["Mes"], g["Prediccion"], marker="s", label="Prediccion", color="#c0392b")
    ax.set_xticklabels(g["Mes"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Costo mensual (USD)")
    ax.set_title(f"Valores reales frente a predicciones - prueba final 2025\nSerie: {serie_top[0]} / {serie_top[1]}")
    ax.legend()
    guardar(fig, "12_real_vs_prediccion.png")


def fig13_residuos():
    pred = pd.read_csv(os.path.join(MODELADO, "predicciones_prueba_final.csv"))
    if pred.empty:
        return
    pred["Residuo"] = pred["Real"] - pred["Prediccion"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(pred["Residuo"], bins=30, color="#2c5f8a")
    ax.axvline(0, color="black", linestyle="--")
    ax.set_xlabel("Residuo (Real - Prediccion, USD)")
    ax.set_ylabel("Frecuencia")
    ax.set_title("Distribucion de residuos - prueba final (todas las series)")
    guardar(fig, "13_residuos.png")


def fig14_importancia_variables():
    imp = pd.read_csv(os.path.join(MODELADO, "importancia_variables.csv"))
    if imp.empty:
        return
    resumen = imp.groupby("Variable")["ImportanciaInterna"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(resumen.index, resumen.values, color="#2c5f8a")
    ax.set_xlabel("Importancia interna promedio (Random Forest / Gradient Boosting)")
    ax.set_title("Importancia de variables (promedio entre series seleccionadas)")
    guardar(fig, "14_importancia_variables.png")


def fig15_shap():
    shap_df = pd.read_csv(os.path.join(MODELADO, "resultados_shap.csv"))
    if shap_df.empty:
        return
    resumen = shap_df.groupby("Variable")["SHAP_MediaAbsoluta"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(resumen.index, resumen.values, color="#27ae60")
    ax.set_xlabel("|SHAP| media promedio entre series")
    ax.set_title("Importancia SHAP de variables (promedio entre series seleccionadas)")
    guardar(fig, "15_shap.png")


def fig16_resultados_prueba_final():
    met = pd.read_csv(os.path.join(MODELADO, "metricas_prueba_final.csv"))
    if met.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    resumen = met.groupby("Modelo")["MAE_USD"].mean().sort_values()
    ax.barh(resumen.index, resumen.values, color="#c0392b")
    ax.set_xlabel("MAE promedio en prueba final 2025 (USD)")
    ax.set_title("Resultados de prueba final por modelo seleccionado")
    guardar(fig, "16_resultados_prueba_final.png")


if __name__ == "__main__":
    funciones = [fig01_flujo_metodologico, fig02_distribucion_registros_por_anio, fig03_cobertura_mensual,
                 fig04_costo_mensual_total, fig05_costo_mensual_por_nave, fig06_costo_mensual_por_categoria,
                 fig07_distribucion_subtotal, fig08_pareto_costos, fig09_clasificacion_adi_cv2,
                 fig10_esquema_walk_forward, fig11_metricas_validacion_por_modelo, fig12_real_vs_prediccion,
                 fig13_residuos, fig14_importancia_variables, fig15_shap, fig16_resultados_prueba_final]
    for fn in funciones:
        try:
            fn()
            print("OK:", fn.__name__)
        except Exception as e:
            print("ERROR:", fn.__name__, e)
