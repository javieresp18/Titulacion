"""
Verificacion final de consistencia: controles de fidelidad metodologica,
calidad, conciliacion, prevencion de fuga de informacion temporal y busqueda
textual recursiva de referencias prohibidas a otras ejecuciones.
"""
import os
import re

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATRONES_PROHIBIDOS = [
    r"\bv1\b", r"\bv2\b", r"\bv3\b", r"\bv4\b",
    r"versi[oó]n anterior", r"ejecuci[oó]n anterior", r"ejecuci[oó]n previa",
    r"dataset anterior", r"resultados anteriores", r"resultados previos",
    r"sin 2024", r"incorpora 2024", r"incorporaci[oó]n de 2024",
    r"fase\s*8", r"fase\s*9", r"fase\s*10",
    r"comparaci[oó]n de versiones", r"reemplaza a", r"respecto de la ejecuci[oó]n",
    r"anteriormente", r"reprocesamiento", r"reejecuci[oó]n",
]
# 'historico'/'historica' se permite cuando se refiere a registros de mantenimiento;
# se marca solo si aparece junto a palabras que sugieren version del proyecto.
PATRON_HISTORICO_SOSPECHOSO = r"(versi[oó]n|ejecuci[oó]n)\s+hist[oó]ric[ao]"

EXTENSIONES = (".md", ".py", ".csv", ".json", ".txt", ".html")
EXCLUIR_DIRS = {"restringido", ".git"}
# Este propio script contiene los patrones como literales de deteccion; no se
# audita a si mismo. Los archivos que son extractos textuales directos del
# dataset oficial (descripciones originales de repuestos, p. ej.
# "reemplaza al ..." referido a numeros de parte fisicos) tampoco se evaluan
# contra el patron generico "reemplaza a", pues se trata de vocabulario de
# dominio (equivalencias entre repuestos) y no de referencias a versiones o
# ejecuciones del proyecto.
ARCHIVOS_EXCLUIDOS = {"verificar_consistencia.py"}
PATRONES_TEXTO_LIBRE_DATASET = {"reemplaza a"}
ARCHIVOS_TEXTO_LIBRE_DATASET = {"validacion_codigos_descripciones.csv", "dataset_depurado_anonimizado.csv",
                                 "serie_items_mensual.csv", "clasificacion_adi_cv2.csv", "items_elegibles.csv"}


def escanear():
    hallazgos = []
    for root, dirs, files in os.walk(RUTA_BASE):
        dirs[:] = [d for d in dirs if d not in EXCLUIR_DIRS]
        if "Resultados_Proyecto_Mantenimiento_Naval" not in root:
            continue
        for fname in files:
            if not fname.lower().endswith(EXTENSIONES):
                continue
            if fname in ARCHIVOS_EXCLUIDOS:
                continue
            ruta = os.path.join(root, fname)
            try:
                with open(ruta, encoding="utf-8", errors="ignore") as f:
                    contenido = f.read()
            except Exception:
                continue
            texto_lower = contenido.lower()
            for patron in PATRONES_PROHIBIDOS:
                if patron in PATRONES_TEXTO_LIBRE_DATASET and fname in ARCHIVOS_TEXTO_LIBRE_DATASET:
                    continue
                for m in re.finditer(patron, texto_lower):
                    hallazgos.append({"archivo": ruta, "patron": patron, "contexto": texto_lower[max(0, m.start()-40):m.end()+40]})
            for m in re.finditer(PATRON_HISTORICO_SOSPECHOSO, texto_lower):
                hallazgos.append({"archivo": ruta, "patron": PATRON_HISTORICO_SOSPECHOSO, "contexto": texto_lower[max(0, m.start()-40):m.end()+40]})
            # nombres de archivo/carpeta
            for patron in PATRONES_PROHIBIDOS:
                if re.search(patron, fname.lower()):
                    hallazgos.append({"archivo": ruta, "patron": patron + " (nombre de archivo)", "contexto": fname})
    return hallazgos


if __name__ == "__main__":
    hallazgos = escanear()
    if hallazgos:
        print(f"Se encontraron {len(hallazgos)} referencias potencialmente prohibidas:")
        for h in hallazgos:
            print(h)
    else:
        print("Verificacion de referencias prohibidas: sin hallazgos.")
