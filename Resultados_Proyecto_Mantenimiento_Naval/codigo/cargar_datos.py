"""
Carga y control del dataset oficial de la investigacion.

Fuente oficial de datos: Data-set.xlsx
Este script no asume cifras: todo se calcula directamente desde el archivo.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

import pandas as pd

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DATASET = os.path.join(RUTA_BASE, "Dataset.xlsx")
RUTA_CONTROL = os.path.join(RUTA_BASE, "control", "control_ejecucion.json")
RUTA_DICCIONARIO = os.path.join(RUTA_BASE, "control", "diccionario_datos.csv")

COLUMNAS_ESPERADAS = [
    "FechaCont", "Cardcode", "CardName", "ItemCode", "ItemDescripcion",
    "ItemDetalles", "Quantity", "PrecioUnitarioSinDescuento",
    "DescuentoUnitario", "PrecioUnitario", "SubTotal", "Unidad", "Tipo",
    "ParteTecnica",
]


def sha256_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar_dataset():
    """Carga el dataset oficial y devuelve el DataFrame crudo (sin depurar)."""
    xls = pd.ExcelFile(RUTA_DATASET)
    hoja = xls.sheet_names[0]
    df = pd.read_excel(RUTA_DATASET, sheet_name=hoja)
    return df, hoja, xls.sheet_names


def generar_control_ejecucion():
    df, hoja, hojas = cargar_dataset()

    faltantes = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    sobrantes = [c for c in df.columns if c not in COLUMNAS_ESPERADAS]

    fechas = pd.to_datetime(df["FechaCont"], errors="coerce")
    reg_por_anio = fechas.dt.year.value_counts(dropna=False).sort_index().to_dict()
    reg_por_anio = {str(int(k)): int(v) for k, v in reg_por_anio.items() if pd.notna(k)}
    reg_por_mes = fechas.dt.to_period("M").value_counts(dropna=False).sort_index()
    reg_por_mes = {str(k): int(v) for k, v in reg_por_mes.items()}

    control = {
        "descripcion": "El estudio se ejecuto sobre Data-set.xlsx, definido como fuente oficial de datos de la investigacion.",
        "archivo": {
            "nombre_exacto": "Dataset.xlsx",
            "hoja_utilizada": hoja,
            "numero_hojas": len(hojas),
            "nombres_hojas": hojas,
            "hash_sha256": sha256_archivo(RUTA_DATASET),
            "tamano_bytes": os.path.getsize(RUTA_DATASET),
        },
        "estructura": {
            "numero_filas": int(df.shape[0]),
            "numero_columnas": int(df.shape[1]),
            "encabezados": df.columns.tolist(),
            "columnas_esperadas_faltantes": faltantes,
            "columnas_no_esperadas_presentes": sobrantes,
            "tipos_datos": {c: str(t) for c, t in df.dtypes.items()},
        },
        "cobertura_temporal": {
            "fecha_minima": str(fechas.min()),
            "fecha_maxima": str(fechas.max()),
            "registros_por_anio": reg_por_anio,
            "registros_por_mes": reg_por_mes,
            "registros_con_fecha_invalida": int(fechas.isna().sum()),
        },
        "dimensiones_clave": {
            "numero_naves_unidad_unica": int(df["Unidad"].nunique(dropna=True)),
            "numero_proveedores_unicos_cardcode": int(df["Cardcode"].nunique(dropna=True)),
            "numero_items_unicos_itemcode": int(df["ItemCode"].nunique(dropna=True)),
            "numero_categorias_partetecnica": int(df["ParteTecnica"].nunique(dropna=True)),
            "numero_tipos_unidad": int(df["Tipo"].nunique(dropna=True)),
        },
        "costo_bruto_usd": {
            "subtotal_suma": round(float(df["SubTotal"].sum(skipna=True)), 2),
            "subtotal_nulos": int(df["SubTotal"].isna().sum()),
        },
        "fecha_hora_ejecucion_utc": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(RUTA_CONTROL), exist_ok=True)
    with open(RUTA_CONTROL, "w", encoding="utf-8") as f:
        json.dump(control, f, ensure_ascii=False, indent=2)

    return control, df


def generar_diccionario_datos(df):
    filas = []
    descripciones = {
        "FechaCont": "Fecha contable de la transaccion (posible primer dia del mes en algunos periodos).",
        "Cardcode": "Codigo del socio de negocio (proveedor o tercero) asociado a la transaccion.",
        "CardName": "Nombre del socio de negocio (proveedor o tercero).",
        "ItemCode": "Codigo del item o servicio transaccionado.",
        "ItemDescripcion": "Descripcion general del item o servicio.",
        "ItemDetalles": "Detalle textual libre de la transaccion (observaciones).",
        "Quantity": "Cantidad transaccionada del item.",
        "PrecioUnitarioSinDescuento": "Precio unitario antes de aplicar descuento (USD).",
        "DescuentoUnitario": "Descuento unitario aplicado (USD).",
        "PrecioUnitario": "Precio unitario efectivo despues de descuento (USD).",
        "SubTotal": "Costo total de la linea de transaccion (USD). Variable monetaria principal.",
        "Unidad": "Identificador de la nave o unidad operativa (a anonimizar).",
        "Tipo": "Clasificacion general de la unidad (p. ej. BUQUE, REMOLCADOR).",
        "ParteTecnica": "Categoria tecnica del repuesto o servicio.",
    }
    usos = {
        "FechaCont": "Construccion de series temporales mensuales (calendario).",
        "Cardcode": "Anonimizacion; conteo de proveedores.",
        "CardName": "Anonimizacion; no se conserva en el paquete academico.",
        "ItemCode": "Nivel de analisis individual (series por item).",
        "ItemDescripcion": "Validacion de correspondencia codigo-descripcion.",
        "ItemDetalles": "Auditoria de calidad (texto libre, no estructurado).",
        "Quantity": "Variable de cantidad; construccion de demanda mensual.",
        "PrecioUnitarioSinDescuento": "Validacion monetaria (calculo de costo).",
        "DescuentoUnitario": "Validacion monetaria (calculo de costo).",
        "PrecioUnitario": "Calculo de CostoCalculado = Quantity * PrecioUnitario.",
        "SubTotal": "Variable objetivo monetaria (costo mensual agregado).",
        "Unidad": "Nivel de analisis por nave (anonimizada).",
        "Tipo": "Variable descriptiva de clasificacion de la unidad.",
        "ParteTecnica": "Nivel de analisis por categoria tecnica; criterios de inclusion/exclusion.",
    }
    reglas = {
        "FechaCont": "Debe ser una fecha valida y convertible a datetime.",
        "Quantity": "Se documenta pero no se fuerza a positivo (se reporta si hay negativos/ceros).",
        "PrecioUnitario": "Se contrasta contra PrecioUnitarioSinDescuento - DescuentoUnitario.",
        "SubTotal": "Se contrasta contra Quantity * PrecioUnitario (CostoCalculado).",
    }
    for col in df.columns:
        tipo_original = str(df[col].dtype)
        if col == "FechaCont":
            tipo_convertido = "datetime64[ns]"
        elif col in ("Quantity", "PrecioUnitarioSinDescuento", "DescuentoUnitario", "PrecioUnitario", "SubTotal"):
            tipo_convertido = "float64"
        else:
            tipo_convertido = "string (categorica/texto)"
        filas.append({
            "Variable": col,
            "TipoOriginal": tipo_original,
            "TipoConvertido": tipo_convertido,
            "Descripcion": descripciones.get(col, ""),
            "UsoAnalitico": usos.get(col, ""),
            "ReglaValidacion": reglas.get(col, "Se documenta el porcentaje de nulos y valores unicos."),
            "Transformacion": "Anonimizacion (hash estable)" if col in ("Cardcode", "CardName", "Unidad") else "Ninguna / segun depuracion",
            "Restricciones": "No se renombra ni se elimina sin registro en bitacora.",
            "PorcentajeNulos": round(float(df[col].isna().mean() * 100), 4),
            "NumeroValoresUnicos": int(df[col].nunique(dropna=True)),
        })
    tabla = pd.DataFrame(filas)
    os.makedirs(os.path.dirname(RUTA_DICCIONARIO), exist_ok=True)
    tabla.to_csv(RUTA_DICCIONARIO, index=False, encoding="utf-8-sig")
    return tabla


if __name__ == "__main__":
    control, df = generar_control_ejecucion()
    generar_diccionario_datos(df)
    print(json.dumps(control, indent=2, ensure_ascii=False)[:2000])
