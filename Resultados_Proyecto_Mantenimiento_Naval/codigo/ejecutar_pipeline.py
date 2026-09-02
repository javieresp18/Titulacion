"""
Orquestador del pipeline reproducible completo.

Ejecuta, en orden, la carga y control del dataset, la depuracion, la
construccion de series, el entrenamiento y evaluacion de modelos, la
interpretabilidad, la sensibilidad, las figuras, la documentacion y la
verificacion final de consistencia.
"""
import subprocess
import sys
import time

PASOS = [
    "cargar_datos.py",
    "depurar_datos.py",
    "construir_series.py",
    "entrenar_modelos_agregados.py",
    "entrenar_modelos_intermitentes.py",
    "evaluar_modelos.py",
    "generar_figuras.py",
    "generar_documentacion.py",
    "verificar_consistencia.py",
]

if __name__ == "__main__":
    for paso in PASOS:
        print(f"\n===== Ejecutando {paso} =====")
        t0 = time.time()
        r = subprocess.run([sys.executable, paso])
        print(f"----- {paso} finalizado en {time.time() - t0:.1f}s (codigo {r.returncode}) -----")
        if r.returncode != 0:
            print(f"ERROR: {paso} termino con codigo distinto de cero. Deteniendo pipeline.")
            sys.exit(r.returncode)
    print("\nPipeline completo ejecutado correctamente.")
