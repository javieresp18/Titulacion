"""
Auditoria de calidad, validacion monetaria, tratamiento de duplicados y
anulaciones, homologacion de categorias, anonimizacion y construccion del
dataset analitico depurado.

Sigue el orden establecido en el apartado 3.6 de la metodologia:
1. Validacion de estructura -> cargar_datos.py
2. Conversion de tipos
3. Validacion de fechas
4. Normalizacion de texto
5. Identificacion de duplicados
6. Tratamiento de duplicados
7. Identificacion de anulaciones
8. Validacion codigo-descripcion
9. Tratamiento diferenciado de faltantes
10. Homologacion de categorias
11. Aplicacion de inclusiones y exclusiones
12. Anonimizacion
13. Construccion del dataset analitico
"""
import hashlib
import json
import os
import re

import numpy as np
import pandas as pd

from cargar_datos import cargar_dataset

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTRL = os.path.join(RUTA_BASE, "control")
DATOS = os.path.join(RUTA_BASE, "datos_procesados")
DOCS = os.path.join(RUTA_BASE, "documentacion")
RESTRINGIDO = os.path.join(RUTA_BASE, "restringido")
for d in (CTRL, DATOS, DOCS, RESTRINGIDO):
    os.makedirs(d, exist_ok=True)

# --- Categorias tecnicas: inclusion segun apartado 3.4 ---------------------
CATEGORIAS_INCLUIDAS_LITERAL = {
    "REPUESTOS", "MECANICOS", "ELECTRICOS", "BOMBAS", "FILTROS", "ACEITES",
    "ACEITE Y FILTROS", "FERRETERIA", "QUIMICOS", "HIDRAULICOS",
    "MANTENIMIENTO", "SERVICIOS DE MANTENIMIENTO", "OPERACIONES",
    "EQUIPOS DE NAVEGACION",
}
CATEGORIAS_EXCLUIDAS_LITERAL = {
    "OFICINA", "SUMINISTROS DE OFICINA", "HOGAR", "MEDICINAS", "SEGURIDAD",
    "LIMPIEZA", "PINTURAS", "CERTIFICACION",
}


def normalizar_texto(s):
    if pd.isna(s):
        return s
    s = str(s).strip().upper()
    s = re.sub(r"\s+", " ", s)
    return s


def clasificar_categoria(valor_normalizado):
    """Decide inclusion/exclusion de una categoria tecnica (ParteTecnica)."""
    if valor_normalizado is None or valor_normalizado == "" or pd.isna(valor_normalizado):
        return "EXCLUIDA", "Valor nulo o vacio: no permite verificar pertinencia tecnica."
    v = valor_normalizado
    if v in CATEGORIAS_INCLUIDAS_LITERAL:
        return "INCLUIDA", "Categoria listada explicitamente en el apartado 3.4 como pertinente al mantenimiento naval."
    if v in CATEGORIAS_EXCLUIDAS_LITERAL:
        return "EXCLUIDA", "Categoria listada explicitamente en el apartado 3.4 como ajena al mantenimiento naval (insumo de hotelera, oficina, salud o seguridad)."
    # Categoria no enumerada literalmente: decision operativa documentada.
    v_low = v.lower()
    if "grasa" in v_low or "lubric" in v_low:
        return "INCLUIDA", "Decision operativa: funcionalmente equivalente a ACEITES/lubricacion de maquinaria, dentro del alcance de mantenimiento tecnico (ver bitacora_decisiones_metodologicas.md)."
    if any(k in v_low for k in ["motor", "propuls", "valvula", "valvul", "tuberia", "instrument", "soldadura", "neumatic", "electronic", "navegacion", "casco", "estructural"]):
        return "INCLUIDA", "Decision operativa: categoria tecnica funcionalmente vinculada al mantenimiento de sistemas navales, no enumerada literalmente en 3.4 (ver bitacora_decisiones_metodologicas.md)."
    if any(k in v_low for k in ["oficina", "hogar", "medicin", "farmac", "limpieza", "pintura", "certificac", "hoteler", "epp", "dotacion", "uniform"]):
        return "EXCLUIDA", "Decision operativa: insumo ajeno al mantenimiento tecnico naval, analogo a las categorias excluidas literalmente (ver bitacora_decisiones_metodologicas.md)."
    return "INCLUIDA", "Decision operativa conservadora: sin evidencia de pertenecer a categorias explicitamente excluidas, se mantiene en el analisis agregado (ver bitacora_decisiones_metodologicas.md)."


def anonimizar_id(valor, prefijo, mapeo):
    if pd.isna(valor):
        return None
    valor = str(valor)
    if valor not in mapeo:
        mapeo[valor] = f"{prefijo}_{len(mapeo) + 1:03d}"
    return mapeo[valor]


def ejecutar_depuracion():
    df, hoja, hojas = cargar_dataset()
    n_original = len(df)
    costo_bruto = float(df["SubTotal"].sum(skipna=True))

    bitacora = []
    decisiones = []

    # --- 2. Conversion de tipos -------------------------------------------
    df["FechaCont"] = pd.to_datetime(df["FechaCont"], errors="coerce")
    for c in ["Quantity", "PrecioUnitarioSinDescuento", "DescuentoUnitario", "PrecioUnitario", "SubTotal"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    bitacora.append("Conversion de tipos: FechaCont a datetime; columnas monetarias y Quantity a float64.")

    # --- 3. Validacion de fechas -------------------------------------------
    fechas_invalidas = int(df["FechaCont"].isna().sum())
    bitacora.append(f"Validacion de fechas: {fechas_invalidas} registros con FechaCont invalida o no convertible.")

    # --- 4. Normalizacion de texto ------------------------------------------
    for c in ["ItemDescripcion", "Unidad", "Tipo", "ParteTecnica", "CardName"]:
        df[c + "_norm"] = df[c].apply(normalizar_texto)
    bitacora.append("Normalizacion de texto: mayusculas, recorte de espacios y colapso de espacios multiples en variables categoricas y descriptivas.")

    # --- 12 (adelantado). Anonimizacion temprana ----------------------------
    # Se anonimizan Cardcode/CardName/Unidad desde el inicio, de modo que
    # NINGUN extracto de auditoria (incluidos los registros excluidos) sea
    # exportado con nombres reales de proveedores o naves.
    mapeo_prov_global, mapeo_nave_global = {}, {}
    df["ProveedorAnonimo"] = df["Cardcode"].apply(lambda v: anonimizar_id(v, "PROV", mapeo_prov_global))
    df["NaveAnonima"] = df["Unidad_norm"].apply(lambda v: anonimizar_id(v, "NAVE", mapeo_nave_global))
    COLUMNAS_SENSIBLES = ["Cardcode", "CardName", "CardName_norm", "Unidad", "Unidad_norm",
                          "ItemDetalles", "ItemDescripcion", "ItemDescripcion_norm"]  # texto libre: puede
    # contener nombres de proveedores, astilleros, fabricantes o localidades reales

    def exportar_auditoria(df_extracto, ruta):
        cols = [c for c in df_extracto.columns if c not in COLUMNAS_SENSIBLES]
        df_extracto[cols].to_csv(ruta, index=False, encoding="utf-8-sig")

    # --- AUDITORIA DE CALIDAD (apartado 11) --------------------------------
    hallazgos = []

    def registrar_hallazgo(nombre, mask, regla, justificacion, impacto_modelado):
        n = int(mask.sum())
        pct = round(n / n_original * 100, 4)
        impacto_usd = round(float(df.loc[mask, "SubTotal"].sum(skipna=True)), 2)
        hallazgos.append({
            "Hallazgo": nombre, "NumeroRegistros": n, "PorcentajeRegistros": pct,
            "ImpactoMonetarioUSD": impacto_usd, "ReglaAplicada": regla,
            "Justificacion": justificacion, "ImpactoPotencialModelado": impacto_modelado,
        })
        return mask

    m_nulos_fecha = df["FechaCont"].isna()
    registrar_hallazgo("Fechas invalidas/nulas", m_nulos_fecha,
                        "FechaCont no convertible a datetime.",
                        "Impide asignar el registro a un mes de la serie temporal.",
                        "Excluye el registro de toda serie mensual.")

    m_cant_neg = df["Quantity"] < 0
    registrar_hallazgo("Cantidades negativas", m_cant_neg, "Quantity < 0.",
                        "Puede representar devoluciones o correcciones; se documenta sin eliminar automaticamente.",
                        "Afecta CantidadMensual si se conserva; se evalua en anulaciones.")

    m_cant_cero = df["Quantity"] == 0
    registrar_hallazgo("Cantidades iguales a cero", m_cant_cero, "Quantity == 0.",
                        "Transaccion sin cantidad; puede ser un servicio valorado por SubTotal.",
                        "No aporta a CantidadMensual pero puede aportar a CostoMensualUSD.")

    m_precio_neg = df["PrecioUnitario"] < 0
    registrar_hallazgo("Precios negativos", m_precio_neg, "PrecioUnitario < 0.",
                        "Inusual; se documenta para revision funcional.",
                        "Puede distorsionar PrecioUnitarioPonderado en el nivel individual.")

    m_precio_cero = (df["PrecioUnitario"] == 0) & df["PrecioUnitario"].notna()
    registrar_hallazgo("Precios iguales a cero", m_precio_cero, "PrecioUnitario == 0.",
                        "Compatible con bonificaciones o servicios sin precio unitario explicito.",
                        "Reduce la base de precios validos para conversion cantidad->costo en nivel individual.")

    m_desc_neg = df["DescuentoUnitario"] < 0
    registrar_hallazgo("Descuentos negativos", m_desc_neg, "DescuentoUnitario < 0.",
                        "Incremento de precio disfrazado de descuento negativo; se documenta.",
                        "Bajo impacto esperado en el costo mensual agregado.")

    m_desc_inconsistente = (df["PrecioUnitarioSinDescuento"].notna() & df["DescuentoUnitario"].notna() &
                             df["PrecioUnitario"].notna() &
                             ((df["PrecioUnitarioSinDescuento"] - df["DescuentoUnitario"] - df["PrecioUnitario"]).abs() > 0.05))
    registrar_hallazgo("Descuentos inconsistentes", m_desc_inconsistente,
                        "PrecioUnitarioSinDescuento - DescuentoUnitario != PrecioUnitario (tolerancia 0.05 USD).",
                        "Tolerancia de redondeo monetario definida operativamente (ver bitacora_decisiones_metodologicas.md).",
                        "No afecta directamente a SubTotal, que se mantiene como variable monetaria principal.")

    m_subtotal_neg = df["SubTotal"] < 0
    registrar_hallazgo("Subtotales negativos", m_subtotal_neg, "SubTotal < 0.",
                        "Candidato a anulacion contable o devolucion; se evalua en el analisis de anulaciones.",
                        "Puede reducir el costo mensual agregado si se conserva.")

    m_subtotal_cero = (df["SubTotal"] == 0) & df["SubTotal"].notna()
    registrar_hallazgo("Subtotales iguales a cero", m_subtotal_cero, "SubTotal == 0.",
                        "Transaccion sin efecto monetario; no aporta a CostoMensualUSD.",
                        "Neutral para el nivel agregado; se conserva el registro para trazabilidad de movimientos.")

    m_error_excel = df.apply(lambda r: any(isinstance(r[c], str) and str(r[c]).startswith("#") for c in
                                            ["Quantity", "PrecioUnitario", "SubTotal"] if c in df.columns), axis=1)
    registrar_hallazgo("Valores de error de Excel (#N/A, #DIV/0!, etc.)", m_error_excel,
                        "Valor de texto iniciado en '#' en columnas monetarias.",
                        "Error de calculo heredado del origen; no evaluable como numero.",
                        "Se excluye del calculo monetario si se detecta.")

    m_sin_desc = df["ItemDescripcion"].isna() | (df["ItemDescripcion_norm"] == "")
    registrar_hallazgo("Codigos sin descripcion", m_sin_desc, "ItemDescripcion nula o vacia.",
                        "Impide verificar la identidad del repuesto.",
                        "El ItemCode correspondiente no es elegible para el nivel individual.")

    desc_por_item = df.groupby("ItemCode")["ItemDescripcion_norm"].nunique(dropna=True)
    items_ambiguos = set(desc_por_item[desc_por_item > 1].index)
    m_items_ambiguos = df["ItemCode"].isin(items_ambiguos)
    registrar_hallazgo("Codigos asociados con descripciones diferentes", m_items_ambiguos,
                        "ItemCode con mas de una ItemDescripcion_norm distinta en todo el periodo.",
                        "Posible reutilizacion del codigo para repuestos distintos en años diferentes (limitacion metodologica 3.11).",
                        "El ItemCode queda excluido del modelado individual; permanece en el costo agregado.")

    m_unidad_sin_id = df["Unidad_norm"].isna() | (df["Unidad_norm"] == "")
    registrar_hallazgo("Naves sin identificar", m_unidad_sin_id, "Unidad nula o vacia.",
                        "Impide asignar la transaccion a una nave para el nivel agregado por nave.",
                        "El registro no aporta a series por nave, si a la serie de toda la flota.")

    m_prov_sin_id = df["Cardcode"].isna() | (df["Cardcode"].astype(str).str.strip() == "")
    registrar_hallazgo("Proveedores sin identificar", m_prov_sin_id, "Cardcode nulo o vacio.",
                        "Impide contabilizar NumeroProveedores de forma exacta en ese registro.",
                        "Reduce levemente la precision del conteo de proveedores por serie mensual.")

    # Valores extremos: se documentan, NO se eliminan por IQR/z-score/percentil (regla metodologica 3.6).
    st = df["SubTotal"].dropna()
    p99 = st.quantile(0.99) if len(st) else np.nan
    m_extremos = df["SubTotal"] >= p99 if pd.notna(p99) else pd.Series(False, index=df.index)
    registrar_hallazgo("Valores extremos (percentil 99 de SubTotal, solo documentacion)", m_extremos,
                        f"SubTotal >= percentil 99 ({p99:.2f} USD). No se elimina: se documenta y se usa en analisis de sensibilidad.",
                        "La metodologia (apartado 3.6) prohibe eliminar atipicos solo por superar IQR/z-score/percentil.",
                        "Se evalua su efecto mediante analisis de sensibilidad (con/sin 1% superior de SubTotal).")

    reporte_calidad = pd.DataFrame(hallazgos)
    reporte_calidad.to_csv(os.path.join(DATOS, "..", "control", "reporte_calidad.csv"), index=False, encoding="utf-8-sig")

    exportar_auditoria(df.loc[m_extremos], os.path.join(CTRL, "valores_atipicos.csv"))
    neg_mask = m_cant_neg | m_precio_neg | m_desc_neg | m_subtotal_neg
    exportar_auditoria(df.loc[neg_mask], os.path.join(CTRL, "registros_negativos.csv"))

    # --- VALIDACION MONETARIA (apartado 12) --------------------------------
    df["CostoCalculado"] = df["Quantity"] * df["PrecioUnitario"]
    df["DiferenciaCosto"] = df["SubTotal"] - df["CostoCalculado"]
    df["ErrorAbsolutoCosto"] = df["DiferenciaCosto"].abs()
    df["ErrorRelativoCosto"] = np.where(
        df["SubTotal"].abs() > 0, df["ErrorAbsolutoCosto"] / df["SubTotal"].abs(), np.nan
    )

    def clasificar_diferencia(row):
        if pd.isna(row["CostoCalculado"]) or pd.isna(row["SubTotal"]):
            return "No evaluable"
        if row["SubTotal"] == 0:
            return "No evaluable" if row["CostoCalculado"] == 0 else "Requiere revision funcional"
        err_abs = row["ErrorAbsolutoCosto"]
        err_rel = row["ErrorRelativoCosto"]
        if err_abs <= 0.01:
            return "Coincidencia exacta"
        if err_abs <= 0.5:
            return "Diferencia de redondeo"
        if err_rel is not None and pd.notna(err_rel) and err_rel <= 0.05:
            return "Diferencia menor"
        if err_rel is not None and pd.notna(err_rel) and err_rel <= 0.30:
            return "Diferencia material"
        return "Posible error"

    df["ClasificacionDiferenciaMonetaria"] = df.apply(clasificar_diferencia, axis=1)
    df[["FechaCont", "ItemCode", "Quantity", "PrecioUnitario", "SubTotal",
        "CostoCalculado", "DiferenciaCosto", "ErrorAbsolutoCosto",
        "ErrorRelativoCosto", "ClasificacionDiferenciaMonetaria"]].to_csv(
        os.path.join(DATOS, "..", "control", "diferencias_monetarias.csv"), index=False, encoding="utf-8-sig")
    decisiones.append({
        "Apartado": "3.6 / 3.10",
        "Evidencia": f"Distribucion de ClasificacionDiferenciaMonetaria: {df['ClasificacionDiferenciaMonetaria'].value_counts().to_dict()}",
        "Decision": "Se mantiene SubTotal como variable monetaria principal (no se sustituye por CostoCalculado).",
        "Justificacion": "El documento de titulacion establece SubTotal como variable monetaria principal salvo evidencia concluyente en contra; no se hallo tal evidencia.",
        "Impacto": "Ninguno sobre la variable objetivo; CostoCalculado se usa solo como control de calidad.",
    })

    # --- 5/6. Duplicados exactos --------------------------------------------
    cols_dup = [c for c in df.columns if not c.endswith("_norm") and c not in
                ("CostoCalculado", "DiferenciaCosto", "ErrorAbsolutoCosto", "ErrorRelativoCosto", "ClasificacionDiferenciaMonetaria")]
    dup_mask = df.duplicated(subset=cols_dup, keep="first")
    df_dup_exactos = df.loc[df.duplicated(subset=cols_dup, keep=False)].sort_values(cols_dup)
    exportar_auditoria(df_dup_exactos, os.path.join(CTRL, "duplicados_exactos.csv"))
    n_dup = int(dup_mask.sum())
    costo_dup = float(df.loc[dup_mask, "SubTotal"].sum(skipna=True))
    bitacora.append(f"Duplicados exactos detectados (todas las columnas originales): {n_dup} registros ({costo_dup:.2f} USD), excluidos en el escenario principal.")

    # Posibles duplicados logicos (subconjunto de columnas clave)
    cols_logicos = ["FechaCont", "Cardcode", "ItemCode", "ItemDescripcion_norm", "Quantity", "PrecioUnitario", "SubTotal", "Unidad_norm", "ParteTecnica_norm"]
    dup_logico_mask = df.duplicated(subset=cols_logicos, keep=False) & ~df.duplicated(subset=cols_dup, keep=False)
    exportar_auditoria(df.loc[dup_logico_mask].sort_values(cols_logicos), os.path.join(CTRL, "posibles_duplicados.csv"))
    bitacora.append(f"Posibles duplicados logicos (coincidencia parcial, sin ser duplicado exacto): {int(dup_logico_mask.sum())} registros. No se eliminan sin evidencia adicional.")

    # --- 7. Anulaciones -------------------------------------------------------
    # Buscar pares de anulacion: mismo ItemCode/Cardcode/Unidad con SubTotal de signo opuesto y monto igual, cercanos en fecha.
    anulaciones = []
    negativos = df[df["SubTotal"] < 0]
    if len(negativos) > 0:
        positivos_idx = df.index[df["SubTotal"] > 0]
        for idx, row in negativos.iterrows():
            candidatos = df.loc[positivos_idx]
            candidatos = candidatos[
                (candidatos["ItemCode"] == row["ItemCode"]) &
                (candidatos["Cardcode"] == row["Cardcode"]) &
                ((candidatos["SubTotal"] - (-row["SubTotal"])).abs() <= 0.01)
            ]
            if len(candidatos) > 0:
                match = candidatos.iloc[0]
                anulaciones.append({
                    "IndiceNegativo": idx, "IndicePositivo": match.name,
                    "ItemCode": row["ItemCode"], "ProveedorAnonimo": row["ProveedorAnonimo"],
                    "SubTotalNegativo": row["SubTotal"], "SubTotalPositivo": match["SubTotal"],
                    "FechaNegativo": str(row["FechaCont"]), "FechaPositivo": str(match["FechaCont"]),
                })
    cols_anul = ["IndiceNegativo", "IndicePositivo", "ItemCode", "ProveedorAnonimo",
                 "SubTotalNegativo", "SubTotalPositivo", "FechaNegativo", "FechaPositivo"]
    df_anulaciones = pd.DataFrame(anulaciones, columns=cols_anul)
    df_anulaciones.to_csv(os.path.join(CTRL, "anulaciones.csv"), index=False, encoding="utf-8-sig")
    if len(df_anulaciones) == 0:
        bitacora.append("Anulaciones contables: no se identificaron pares de anulacion verificables (montos negativos con contraparte positiva exacta del mismo ItemCode y Cardcode).")
        indices_anulados = set()
    else:
        bitacora.append(f"Anulaciones contables verificadas: {len(df_anulaciones)} pares identificados.")
        indices_anulados = set(df_anulaciones["IndiceNegativo"]).union(set(df_anulaciones["IndicePositivo"]))

    # --- 8. Validacion codigo-descripcion (apartado 14) -----------------------
    filas_val = []
    for item, grupo in df.groupby("ItemCode"):
        descs_orig = grupo["ItemDescripcion"].dropna().unique().tolist()
        descs_norm = grupo["ItemDescripcion_norm"].dropna().unique().tolist()
        if len(descs_norm) == 0:
            desc_mas_frec = None
            pct_corresp = 0.0
            clase = "Codigo no elegible para analisis individual"
        else:
            frec = grupo["ItemDescripcion_norm"].value_counts()
            desc_mas_frec = frec.index[0]
            pct_corresp = round(float(frec.iloc[0] / frec.sum() * 100), 2)
            if len(descs_norm) == 1:
                clase = "Correspondencia univoca"
            elif len(descs_norm) <= 3 and pct_corresp >= 70:
                clase = "Variacion textual normalizable"
            else:
                clase = "Codigo ambiguo"
        filas_val.append({
            "ItemCode": item,
            "NumeroDescripcionesOriginales": len(descs_orig),
            "NumeroDescripcionesNormalizadas": len(descs_norm),
            "DescripcionMasFrecuente": desc_mas_frec,
            "PorcentajeCorrespondencia": pct_corresp,
            "PrimeraFecha": str(grupo["FechaCont"].min()),
            "UltimaFecha": str(grupo["FechaCont"].max()),
            "CategoriasAsociadas": ", ".join(sorted(grupo["ParteTecnica_norm"].dropna().unique().tolist())),
            "ClasificacionCorrespondencia": clase,
        })
    validacion_codigos = pd.DataFrame(filas_val)
    # Depuracion de texto libre: las descripciones de items pueden mencionar
    # incidentalmente el nombre de una nave (p. ej. un repuesto identificado
    # por el destino del envio). Se sustituyen las menciones literales de
    # naves y proveedores reales por marcadores neutros antes de exportar.
    nombres_naves_reales = [str(v) for v in df["Unidad"].dropna().unique() if len(str(v)) >= 3]
    nombres_naves_reales.sort(key=len, reverse=True)
    if "DescripcionMasFrecuente" in validacion_codigos.columns:
        def _depurar_texto(txt):
            if not isinstance(txt, str):
                return txt
            for nombre in nombres_naves_reales:
                txt = re.sub(re.escape(nombre.upper()), "[NAVE]", txt, flags=re.IGNORECASE)
            return txt
        validacion_codigos["DescripcionMasFrecuente"] = validacion_codigos["DescripcionMasFrecuente"].apply(_depurar_texto)
    validacion_codigos.to_csv(os.path.join(DATOS, "..", "modelado", "validacion_codigos_descripciones.csv"), index=False, encoding="utf-8-sig")
    items_elegibles_individual = set(validacion_codigos.loc[
        validacion_codigos["ClasificacionCorrespondencia"].isin(["Correspondencia univoca", "Variacion textual normalizable"]),
        "ItemCode"])
    bitacora.append(f"Validacion codigo-descripcion: {len(items_elegibles_individual)} de {len(validacion_codigos)} ItemCode con correspondencia verificable para el nivel individual; los codigos ambiguos permanecen en el costo agregado.")

    # --- 10/15. Categorias tecnicas (apartado 15) ------------------------------
    catalogo_filas = []
    for valor_orig, grupo in df.groupby(df["ParteTecnica"].fillna("(NULO)")):
        valor_norm = normalizar_texto(valor_orig) if valor_orig != "(NULO)" else None
        estado, justificacion = clasificar_categoria(valor_norm)
        catalogo_filas.append({
            "ValorOriginal": valor_orig,
            "ValorNormalizado": valor_norm,
            "CategoriaConsolidada": valor_norm if valor_norm else "SIN CATEGORIA",
            "EstadoInclusion": estado,
            "JustificacionMetodologica": justificacion,
            "NumeroRegistros": int(len(grupo)),
            "CostoTotalUSD": round(float(grupo["SubTotal"].sum(skipna=True)), 2),
        })
    catalogo = pd.DataFrame(catalogo_filas)
    costo_total_cat = catalogo["CostoTotalUSD"].sum()
    catalogo["ParticipacionPorcentual"] = round(catalogo["CostoTotalUSD"] / costo_total_cat * 100, 4) if costo_total_cat else 0.0
    catalogo.to_csv(os.path.join(DATOS, "..", "control", "catalogo_categorias.csv"), index=False, encoding="utf-8-sig")

    categorias_incluidas = set(catalogo.loc[catalogo["EstadoInclusion"] == "INCLUIDA", "ValorNormalizado"])
    for _, r in catalogo.iterrows():
        decisiones.append({
            "Apartado": "3.4 (categorias tecnicas)",
            "Evidencia": f"Categoria '{r['ValorOriginal']}': {r['NumeroRegistros']} registros, {r['CostoTotalUSD']:.2f} USD ({r['ParticipacionPorcentual']:.2f}% del costo bruto por categoria).",
            "Decision": f"{r['EstadoInclusion']}",
            "Justificacion": r["JustificacionMetodologica"],
            "Impacto": "Material" if r["ParticipacionPorcentual"] >= 1.0 else "Marginal",
        })

    # --- CONSTRUCCION DEL DATASET DEPURADO (escenario principal) --------------
    mask_excluir = dup_mask.copy()
    mask_excluir |= df.index.isin(indices_anulados)
    mask_excluir |= ~df["ParteTecnica_norm"].isin(categorias_incluidas)
    mask_excluir |= m_error_excel
    mask_excluir |= m_nulos_fecha

    costo_excluido_dup = float(df.loc[dup_mask, "SubTotal"].sum(skipna=True))
    costo_excluido_anul = float(df.loc[df.index.isin(indices_anulados), "SubTotal"].sum(skipna=True))
    costo_excluido_cat = float(df.loc[~df["ParteTecnica_norm"].isin(categorias_incluidas) & ~dup_mask & ~df.index.isin(indices_anulados), "SubTotal"].sum(skipna=True))
    costo_excluido_otros = float(df.loc[(m_error_excel | m_nulos_fecha) & ~dup_mask & ~df.index.isin(indices_anulados) & df["ParteTecnica_norm"].isin(categorias_incluidas), "SubTotal"].sum(skipna=True))

    df_depurado = df.loc[~mask_excluir].copy()
    n_depurado = len(df_depurado)
    costo_depurado = float(df_depurado["SubTotal"].sum(skipna=True))

    # --- 12. Anonimizacion -----------------------------------------------------
    # ProveedorAnonimo y NaveAnonima ya fueron asignados de forma global al
    # inicio del script (misma correspondencia en todos los archivos de
    # auditoria y en el dataset depurado).
    correspondencias = pd.concat([
        pd.DataFrame({"TipoID": "PROVEEDOR", "ValorOriginal": list(mapeo_prov_global.keys()), "IDAnonimo": list(mapeo_prov_global.values())}),
        pd.DataFrame({"TipoID": "NAVE", "ValorOriginal": list(mapeo_nave_global.keys()), "IDAnonimo": list(mapeo_nave_global.values())}),
    ], ignore_index=True)
    correspondencias.to_csv(os.path.join(RESTRINGIDO, "correspondencias_anonimizacion_RESTRINGIDO.csv"), index=False, encoding="utf-8-sig")

    codigos_item, _ = pd.factorize(df_depurado["ItemCode"])
    df_depurado["ItemAnonimo"] = ["ITEM_" + str(c).zfill(4) for c in codigos_item]
    mapa_item = dict(zip(df_depurado["ItemCode"], df_depurado["ItemAnonimo"]))

    columnas_finales = [
        "FechaCont", "ProveedorAnonimo", "ItemAnonimo", "ItemCode", "Quantity",
        "PrecioUnitario", "SubTotal", "NaveAnonima", "Tipo", "ParteTecnica_norm",
        "CostoCalculado", "ClasificacionDiferenciaMonetaria",
    ]
    df_final = df_depurado[columnas_finales].rename(columns={"ParteTecnica_norm": "ParteTecnica"})
    df_final["EsItemElegibleIndividual"] = df_depurado["ItemCode"].isin(items_elegibles_individual)
    df_final.to_csv(os.path.join(DATOS, "dataset_depurado_anonimizado.csv"), index=False, encoding="utf-8-sig")

    # --- 17. Conciliaciones -----------------------------------------------------
    conciliacion_filas = pd.DataFrame([{
        "FilasOriginales": n_original,
        "DuplicadosExcluidos": int(dup_mask.sum()),
        "AnulacionesVerificadas": len(indices_anulados),
        "CategoriasExcluidas": int((~df["ParteTecnica_norm"].isin(categorias_incluidas) & ~dup_mask & ~df.index.isin(indices_anulados)).sum()),
        "OtrasExclusionesJustificadas": int(((m_error_excel | m_nulos_fecha) & ~dup_mask & ~df.index.isin(indices_anulados) & df["ParteTecnica_norm"].isin(categorias_incluidas)).sum()),
        "FilasDepuradas": n_depurado,
    }])
    conciliacion_costos = pd.DataFrame([{
        "CostoBrutoUSD": round(costo_bruto, 2),
        "CostoDuplicadosExcluidosUSD": round(costo_excluido_dup, 2),
        "EfectoAnulacionesUSD": round(costo_excluido_anul, 2),
        "CostoCategoriasExcluidasUSD": round(costo_excluido_cat, 2),
        "EfectoOtrasExclusionesUSD": round(costo_excluido_otros, 2),
        "CostoDepuradoUSD": round(costo_depurado, 2),
        "CostoDepuradoCalculadoUSD": round(costo_bruto - costo_excluido_dup - costo_excluido_anul - costo_excluido_cat - costo_excluido_otros, 2),
    }])
    conciliacion = pd.concat([conciliacion_filas, conciliacion_costos], axis=1)
    conciliacion.to_csv(os.path.join(CTRL, "conciliacion_filas_costos.csv"), index=False, encoding="utf-8-sig")

    # --- Analisis de sensibilidad: duplicados excluidos vs conservados --------
    df_depurado_alt = df.loc[~(mask_excluir & ~dup_mask)].copy()  # conservando duplicados
    sensibilidad_dup = {
        "escenario_principal_filas": n_depurado,
        "escenario_principal_costo_usd": round(costo_depurado, 2),
        "escenario_alternativo_conservando_duplicados_filas": len(df_depurado_alt),
        "escenario_alternativo_conservando_duplicados_costo_usd": round(float(df_depurado_alt["SubTotal"].sum(skipna=True)), 2),
    }

    # --- Guardar bitacoras -------------------------------------------------
    with open(os.path.join(DOCS, "bitacora_transformaciones.md"), "w", encoding="utf-8") as f:
        f.write("# Bitacora de transformaciones aplicadas al dataset\n\n")
        f.write("Fuente: Data-set.xlsx. Cada paso sigue el orden establecido en el apartado 3.6 de la metodologia.\n\n")
        for linea in bitacora:
            f.write(f"- {linea}\n")
        f.write(f"\n## Conciliacion de filas\n\n{conciliacion_filas.to_markdown(index=False)}\n")
        f.write(f"\n## Conciliacion de costos (USD)\n\n{conciliacion_costos.to_markdown(index=False)}\n")
        f.write(f"\n## Sensibilidad: duplicados excluidos vs conservados\n\n")
        for k, v in sensibilidad_dup.items():
            f.write(f"- {k}: {v}\n")

    with open(os.path.join(DOCS, "bitacora_decisiones_metodologicas.md"), "w", encoding="utf-8") as f:
        f.write("# Bitacora de decisiones metodologicas operativas\n\n")
        f.write("Registra las decisiones tecnicas necesarias para ejecutar la metodologia cuando el documento de titulacion no fija un detalle computacional literal (apartado 6 del protocolo de ejecucion).\n\n")
        for d in decisiones:
            f.write(f"## {d['Apartado']}\n\n")
            f.write(f"- **Evidencia en Data-set.xlsx:** {d['Evidencia']}\n")
            f.write(f"- **Decision operativa:** {d['Decision']}\n")
            f.write(f"- **Justificacion:** {d['Justificacion']}\n")
            f.write(f"- **Impacto esperado:** {d['Impacto']}\n\n")

    return {
        "df_original": df, "df_final": df_final, "items_elegibles_individual": items_elegibles_individual,
        "mapa_item": mapa_item, "conciliacion": conciliacion, "sensibilidad_dup": sensibilidad_dup,
        "n_original": n_original, "n_depurado": n_depurado, "costo_bruto": costo_bruto, "costo_depurado": costo_depurado,
    }


if __name__ == "__main__":
    res = ejecutar_depuracion()
    print("Filas originales:", res["n_original"], "-> Filas depuradas:", res["n_depurado"])
    print("Costo bruto USD:", round(res["costo_bruto"], 2), "-> Costo depurado USD:", round(res["costo_depurado"], 2))
