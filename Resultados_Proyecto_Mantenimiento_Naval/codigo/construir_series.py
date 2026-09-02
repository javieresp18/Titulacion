"""
Construccion de series mensuales (nivel agregado y nivel individual),
calendario mensual, clasificacion ADI-CV2 e ingenieria de caracteristicas.
"""
import os

import numpy as np
import pandas as pd

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RUTA_BASE, "datos_procesados")
CTRL = os.path.join(RUTA_BASE, "control")
MODELADO = os.path.join(RUTA_BASE, "modelado")
for d in (DATOS, CTRL, MODELADO):
    os.makedirs(d, exist_ok=True)

PERIODO_INICIO = pd.Period("2021-01", freq="M")
PERIODO_FIN = pd.Period("2025-12", freq="M")


def cargar_depurado():
    df = pd.read_csv(os.path.join(DATOS, "dataset_depurado_anonimizado.csv"), parse_dates=["FechaCont"])
    df["Mes"] = df["FechaCont"].dt.to_period("M")
    return df


def construir_calendario(df_original_completo):
    """Calendario mensual 2021-2025 con clasificacion de cobertura, usando el
    dataset ORIGINAL (antes de exclusiones) para no confundir 'sin cobertura'
    con 'excluido por depuracion'."""
    meses = pd.period_range(PERIODO_INICIO, PERIODO_FIN, freq="M")
    df_original_completo["Mes"] = pd.to_datetime(df_original_completo["FechaCont"], errors="coerce").dt.to_period("M")
    conteo = df_original_completo.groupby("Mes").size()
    costo = df_original_completo.groupby("Mes")["SubTotal"].sum()

    filas = []
    for m in meses:
        n_reg = int(conteo.get(m, 0))
        costo_mes = float(costo.get(m, 0.0))
        if n_reg == 0:
            clasificacion = "Sin cobertura verificable"
        elif costo_mes == 0:
            clasificacion = "Observado sin movimientos"
        else:
            clasificacion = "Observado con movimientos"
        filas.append({"Mes": str(m), "NumeroRegistros": n_reg, "CostoTotalUSD": round(costo_mes, 2), "Clasificacion": clasificacion})
    calendario = pd.DataFrame(filas)
    calendario.to_csv(os.path.join(DATOS, "calendario_mensual.csv"), index=False, encoding="utf-8-sig")
    return calendario


def construir_series_agregadas(df):
    def resumen(grupo):
        return pd.Series({
            "CostoMensualUSD": grupo["SubTotal"].sum(),
            "CantidadMensual": grupo["Quantity"].sum(),
            "NumeroMovimientos": len(grupo),
            "NumeroItemsDistintos": grupo["ItemCode"].nunique(),
            "NumeroProveedores": grupo["ProveedorAnonimo"].nunique(),
            "CostoPromedioMovimiento": grupo["SubTotal"].mean(),
            "CostoMedianoMovimiento": grupo["SubTotal"].median(),
            "CostoMaximoMovimiento": grupo["SubTotal"].max(),
        })

    flota = df.groupby("Mes").apply(resumen, include_groups=False).reset_index()
    flota.insert(1, "Nivel", "FLOTA")
    flota.insert(2, "Serie", "FLOTA_TOTAL")

    por_nave = df.groupby(["Mes", "NaveAnonima"]).apply(resumen, include_groups=False).reset_index()
    por_nave.insert(1, "Nivel", "NAVE")
    por_nave["Serie"] = por_nave["NaveAnonima"]

    por_cat = df.groupby(["Mes", "ParteTecnica"]).apply(resumen, include_groups=False).reset_index()
    por_cat.insert(1, "Nivel", "CATEGORIA")
    por_cat["Serie"] = por_cat["ParteTecnica"]

    por_nave_cat = df.groupby(["Mes", "NaveAnonima", "ParteTecnica"]).apply(resumen, include_groups=False).reset_index()
    por_nave_cat.insert(1, "Nivel", "NAVE_CATEGORIA")
    por_nave_cat["Serie"] = por_nave_cat["NaveAnonima"] + " | " + por_nave_cat["ParteTecnica"]

    cols_comunes = ["Mes", "Nivel", "Serie", "CostoMensualUSD", "CantidadMensual", "NumeroMovimientos",
                    "NumeroItemsDistintos", "NumeroProveedores", "CostoPromedioMovimiento",
                    "CostoMedianoMovimiento", "CostoMaximoMovimiento"]
    serie_agregada = pd.concat([
        flota[cols_comunes], por_nave[cols_comunes], por_cat[cols_comunes], por_nave_cat[cols_comunes]
    ], ignore_index=True)
    serie_agregada["Mes"] = serie_agregada["Mes"].astype(str)
    serie_agregada = serie_agregada.sort_values(["Nivel", "Serie", "Mes"])
    serie_agregada.to_csv(os.path.join(DATOS, "serie_agregada_mensual.csv"), index=False, encoding="utf-8-sig")
    return serie_agregada


def determinar_elegibilidad_agregada(serie_agregada, meses_minimos_train=18, meses_minimos_test=6):
    """Una serie (nave, categoria o nave-categoria) es elegible si permite
    conformar entrenamiento+validacion y prueba conforme al protocolo 3.12.
    Decision operativa: minimo 18 meses de entrenamiento/validacion y 6 de
    prueba (documentada en bitacora_decisiones_metodologicas.md)."""
    filas = []
    for (nivel, serie), grupo in serie_agregada.groupby(["Nivel", "Serie"]):
        grupo = grupo.sort_values("Mes")
        n_meses = len(grupo)
        n_meses_positivos = int((grupo["CostoMensualUSD"] > 0).sum())
        elegible = n_meses >= (meses_minimos_train + meses_minimos_test) and n_meses_positivos >= meses_minimos_train
        filas.append({
            "Nivel": nivel, "Serie": serie, "NumeroMesesObservados": n_meses,
            "NumeroMesesConCostoPositivo": n_meses_positivos, "Elegible": elegible,
            "MotivoNoElegibilidad": "" if elegible else "No alcanza el minimo de meses observados/con costo positivo para conformar entrenamiento-validacion y prueba (umbral operativo: 18 y 6 meses).",
        })
    df_eleg = pd.DataFrame(filas)
    df_eleg.to_csv(os.path.join(DATOS, "series_elegibles_agregado.csv"), index=False, encoding="utf-8-sig")
    return df_eleg


def construir_series_items(df):
    items_elegibles_desc = set(df.loc[df["EsItemElegibleIndividual"], "ItemCode"].unique())
    df_items = df[df["ItemCode"].isin(items_elegibles_desc)].copy()

    filas = []
    for (mes, item), grupo in df_items.groupby(["Mes", "ItemCode"]):
        cantidades_validas = grupo.loc[grupo["Quantity"] > 0, "Quantity"]
        precios_validos = grupo.loc[grupo["Quantity"] > 0, ["Quantity", "PrecioUnitario"]].dropna()
        if len(precios_validos) > 0 and precios_validos["Quantity"].sum() > 0:
            precio_ponderado = (precios_validos["Quantity"] * precios_validos["PrecioUnitario"]).sum() / precios_validos["Quantity"].sum()
        else:
            precio_ponderado = np.nan
        filas.append({
            "Mes": str(mes), "ItemAnonimo": grupo["ItemAnonimo"].iloc[0], "ItemCode": item,
            "CantidadMensual": grupo["Quantity"].sum(),
            "CostoMensualUSD": grupo["SubTotal"].sum(),
            "PrecioUnitarioPonderado": precio_ponderado,
            "NumeroMovimientos": len(grupo),
            "NumeroNaves": grupo["NaveAnonima"].nunique(),
            "IndicadorDemandaPositiva": int(grupo["Quantity"].sum() > 0),
        })
    serie_items = pd.DataFrame(filas).sort_values(["ItemAnonimo", "Mes"])
    serie_items.to_csv(os.path.join(DATOS, "serie_items_mensual.csv"), index=False, encoding="utf-8-sig")
    return serie_items


def clasificar_adi_cv2(serie_items, meses_min_train=12, meses_min_test=3, min_demandas_positivas=4):
    """ADI y CV2 segun Syntetos y Boylan (2005). Umbrales: ADI=1.32, CV2=0.49."""
    UMBRAL_ADI = 1.32
    UMBRAL_CV2 = 0.49

    meses_calendario = pd.period_range(PERIODO_INICIO, PERIODO_FIN, freq="M")
    filas = []
    for item, grupo in serie_items.groupby("ItemAnonimo"):
        grupo_num = grupo.set_index(pd.PeriodIndex(grupo["Mes"], freq="M"))[
            ["CantidadMensual", "CostoMensualUSD", "NumeroMovimientos"]
        ].reindex(meses_calendario, fill_value=0)
        grupo = grupo_num
        cantidades = grupo["CantidadMensual"].fillna(0).clip(lower=0)
        meses_obs = int((grupo["NumeroMovimientos"].fillna(0) > 0).sum())
        pos = cantidades[cantidades > 0]
        n_pos = len(pos)
        prop_ceros = round(1 - n_pos / len(cantidades), 4) if len(cantidades) else np.nan

        if n_pos == 0:
            adi, cv2, media_pos, var_pos = np.nan, np.nan, np.nan, np.nan
            clase = "Sin demanda positiva"
        else:
            idx_pos = np.where(cantidades.values > 0)[0]
            intervalos = np.diff(idx_pos)
            adi = float(np.mean(intervalos)) + 1.0 if len(intervalos) > 0 else float(len(cantidades))
            media_pos = float(pos.mean())
            var_pos = float(pos.var(ddof=1)) if n_pos > 1 else 0.0
            cv2 = (var_pos / (media_pos ** 2)) if media_pos > 0 else np.nan
            if pd.isna(cv2):
                clase = "No clasificable"
            elif adi < UMBRAL_ADI and cv2 < UMBRAL_CV2:
                clase = "Suave"
            elif adi >= UMBRAL_ADI and cv2 < UMBRAL_CV2:
                clase = "Intermitente"
            elif adi < UMBRAL_ADI and cv2 >= UMBRAL_CV2:
                clase = "Erratica"
            else:
                clase = "Lumpy"

        elegible = meses_obs >= (meses_min_train + meses_min_test) and n_pos >= min_demandas_positivas
        motivo = "" if elegible else "Meses observados o demandas positivas insuficientes para conformar entrenamiento y prueba (umbral operativo: 15 meses observados, 4 demandas positivas)."

        filas.append({
            "ItemAnonimo": item, "MesesObservados": meses_obs, "MesesConDemandaPositiva": n_pos,
            "ProporcionCeros": prop_ceros, "DemandaMediaPositiva": round(media_pos, 4) if pd.notna(media_pos) else np.nan,
            "VarianzaDemandaPositiva": round(var_pos, 4) if pd.notna(var_pos) else np.nan,
            "ADI": round(adi, 4) if pd.notna(adi) else np.nan, "CV2": round(cv2, 4) if pd.notna(cv2) else np.nan,
            "Clasificacion": clase, "Elegible": elegible, "MotivoNoElegibilidad": motivo,
            "CostoTotalUSD": round(float(grupo["CostoMensualUSD"].sum()), 2),
        })
    clasif = pd.DataFrame(filas)
    clasif.to_csv(os.path.join(DATOS, "clasificacion_adi_cv2.csv"), index=False, encoding="utf-8-sig")

    resumen_clase = clasif.groupby("Clasificacion").agg(
        NumeroItems=("ItemAnonimo", "count"), CostoTotalUSD=("CostoTotalUSD", "sum")).reset_index()
    resumen_clase["ParticipacionPorcentual"] = round(resumen_clase["CostoTotalUSD"] / resumen_clase["CostoTotalUSD"].sum() * 100, 2)
    resumen_clase["UmbralADI"] = UMBRAL_ADI
    resumen_clase["UmbralCV2"] = UMBRAL_CV2
    resumen_clase.to_csv(os.path.join(DATOS, "..", "control", "resumen_clasificacion_adi_cv2.csv"), index=False, encoding="utf-8-sig")

    items_elegibles = clasif.loc[clasif["Elegible"], ["ItemAnonimo", "Clasificacion"]]
    items_elegibles.to_csv(os.path.join(DATOS, "items_elegibles.csv"), index=False, encoding="utf-8-sig")
    return clasif, resumen_clase, items_elegibles


def construir_features_agregado(serie_agregada, series_elegibles):
    """Ingenieria de caracteristicas del apartado 3.6 sobre cada serie elegible del nivel agregado."""
    elegibles_set = set(zip(series_elegibles.loc[series_elegibles["Elegible"], "Nivel"],
                             series_elegibles.loc[series_elegibles["Elegible"], "Serie"]))
    registros_perdidos = []
    todas_filas = []
    for (nivel, serie), grupo in serie_agregada.groupby(["Nivel", "Serie"]):
        if (nivel, serie) not in elegibles_set:
            continue
        g = grupo.sort_values("Mes").reset_index(drop=True)
        g["PeriodoMes"] = pd.PeriodIndex(g["Mes"], freq="M")
        g["MesNumerico"] = g["PeriodoMes"].dt.month
        g["Trimestre"] = g["PeriodoMes"].dt.quarter
        g["Anio"] = g["PeriodoMes"].dt.year
        g["IndiceTemporal"] = np.arange(len(g))

        y = g["CostoMensualUSD"]
        g["Lag1"] = y.shift(1)
        g["Lag2"] = y.shift(2)
        g["Lag3"] = y.shift(3)
        g["Lag12"] = y.shift(12)
        g["MediaMovil3"] = y.shift(1).rolling(3).mean()
        g["MediaMovil6"] = y.shift(1).rolling(6).mean()

        n_perdidas_lag12 = int(g["Lag12"].isna().sum())
        registros_perdidos.append({"Nivel": nivel, "Serie": serie, "TotalMeses": len(g),
                                    "ObservacionesSinLag12": n_perdidas_lag12,
                                    "ObservacionesSinMediaMovil6": int(g["MediaMovil6"].isna().sum())})
        todas_filas.append(g)

    features = pd.concat(todas_filas, ignore_index=True)
    features["Mes"] = features["Mes"].astype(str)
    features = features.drop(columns=["PeriodoMes"])
    features.to_csv(os.path.join(MODELADO, "features_modelado.csv"), index=False, encoding="utf-8-sig")

    reg_perdidas = pd.DataFrame(registros_perdidos)
    reg_perdidas.to_csv(os.path.join(MODELADO, "features_observaciones_perdidas.csv"), index=False, encoding="utf-8-sig")
    return features


if __name__ == "__main__":
    df = cargar_depurado()
    df_original_completo = pd.read_excel(os.path.join(RUTA_BASE, "Dataset.xlsx"), sheet_name="Data-set")
    calendario = construir_calendario(df_original_completo)
    print("Calendario:", calendario["Clasificacion"].value_counts().to_dict())

    serie_agregada = construir_series_agregadas(df)
    print("Serie agregada filas:", len(serie_agregada))

    elegibilidad = determinar_elegibilidad_agregada(serie_agregada)
    print("Elegibilidad agregada:", elegibilidad["Elegible"].value_counts().to_dict())

    serie_items = construir_series_items(df)
    print("Serie items filas:", len(serie_items), "items distintos:", serie_items["ItemAnonimo"].nunique())

    clasif, resumen_clase, items_elegibles = clasificar_adi_cv2(serie_items)
    print(resumen_clase)
    print("Items elegibles nivel individual:", len(items_elegibles))

    features = construir_features_agregado(serie_agregada, elegibilidad)
    print("Features filas:", len(features), "series:", features.groupby(['Nivel','Serie']).ngroups)
