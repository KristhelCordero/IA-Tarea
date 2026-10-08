"""Bateria experimental de escalabilidad para el modulo adicional.

Recorre una rejilla de configuraciones (N x K x semilla), genera las instancias
con el generador parametrizado y ejecuta los agentes sobre ellas, volcando los
resultados en un CSV listo para graficar.

Diseno de la rejilla
--------------------
N y K son los parametros que el estudio debe recorrer. M no es libre: si se
dejara fijo, al crecer N la densidad (M / N^2) caeria y se estaria midiendo a la
vez el efecto del tablero y el de la densidad, que es un factor de dificultad por
derecho propio. Por eso M se fija proporcional a N^2, manteniendo la densidad
constante en todas las celdas de la rejilla y aislando el efecto de N.

Consecuencia a tener presente al leer los resultados: una evaluacion cuesta
O(M * N^2), de modo que con densidad constante el costo crece como N^4, mientras
que K no afecta el costo por evaluacion (solo la dificultad).

Uso
---
    python3 src/modulo_adicional/bateria.py generar
    python3 src/modulo_adicional/bateria.py correr [--agentes evolutivo] [--limite 10]
"""
import argparse
import csv
import os
import random
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(AQUI)
RAIZ = os.path.dirname(SRC)
for ruta in (AQUI, SRC):
    if ruta not in sys.path: sys.path.insert(0, ruta)

from generador_instancias import generar, escribir
from agente_evolutivo.agent import Params, cargar_instancia, decodificar, aptitud, evolucionar

# --- Rejilla experimental --------------------------------------------------
# El enunciado exige al menos tres valores de N, tres de K y tres semillas.
VALORES_N = (4, 6, 8, 10)
VALORES_K = (2, 4, 6)
SEMILLAS = (1, 2, 3)
DENSIDAD = 1.1                      # M = round(DENSIDAD * N^2)

DIR_INSTANCIAS = os.path.join(AQUI, "instancias")
DIR_RESULTADOS = os.path.join(AQUI, "resultados")

def fichas_de(n):
    """Cantidad de fichas para un tablero N x N, a densidad constante."""
    return round(DENSIDAD * n * n)

def nombre_instancia(n, k, semilla):
    return f"N{n:02d}_K{k}_s{semilla}.txt"

def rejilla():
    """Itera las celdas de la rejilla como (n, k, m, semilla, ruta)."""
    for n in VALORES_N:
        for k in VALORES_K:
            for semilla in SEMILLAS:
                yield n, k, fichas_de(n), semilla, os.path.join(DIR_INSTANCIAS, nombre_instancia(n, k, semilla))

# --- Generacion ------------------------------------------------------------

def generar_bateria():
    os.makedirs(DIR_INSTANCIAS, exist_ok = True)
    total = 0
    for n, k, m, semilla, ruta in rejilla():
        escribir(ruta, n, k, generar(n, k, m, semilla),
                 f"bateria escalabilidad N={n} K={k} M={m} semilla={semilla} densidad={m/(n*n):.2f}")
        total += 1
    print(f"{total} instancias escritas en {os.path.relpath(DIR_INSTANCIAS, RAIZ)}")
    print(f"rejilla: N={VALORES_N}  K={VALORES_K}  semillas={SEMILLAS}  densidad={DENSIDAD}")
    for n in VALORES_N:
        print(f"  N={n:2d} -> M={fichas_de(n):3d} fichas sobre {n*n:3d} celdas")

# --- Ejecucion de los agentes ----------------------------------------------
# Cada agente recibe (n, k, fichas, semilla, limite_seg) y devuelve un dict con
# las columnas del CSV. Para incorporar el agente de busqueda basta escribir su
# funcion con esta misma firma y registrarla en AGENTES.

def correr_evolutivo(n, k, fichas, semilla, limite_seg):
    params = Params(limite_seg = limite_seg)
    mejor, metricas = evolucionar(n, fichas, random.Random(semilla), params)
    resultado = decodificar(mejor.cromosoma, n, fichas)
    return {
        "colocadas": resultado.colocadas,
        "ocupadas": resultado.ocupadas,
        "mayor": resultado.mayor,
        "aptitud": mejor.aptitud,
        "tiempo": round(metricas.tiempo, 3),
        "esfuerzo": metricas.evaluaciones,      # evaluaciones de aptitud
        "termino": metricas.motivo_paro != "tiempo",
        "motivo_paro": metricas.motivo_paro,
    }

AGENTES = {
    "evolutivo": correr_evolutivo,
    # "busqueda": correr_busqueda,   <-- pendiente de la implementacion del agente de busqueda
}

COLUMNAS = ["agente", "N", "K", "M", "densidad", "semilla", "colocadas", "total_fichas",
            "ocupadas", "mayor", "aptitud", "tiempo", "esfuerzo", "termino", "motivo_paro"]

def correr_bateria(nombres_agentes, limite_seg, salida):
    faltan = [a for a in nombres_agentes if a not in AGENTES]
    if faltan:
        print(f"agente(s) no registrado(s): {', '.join(faltan)}", file = sys.stderr)
        return 1
    celdas = list(rejilla())
    if not all(os.path.exists(r) for *_, r in celdas):
        print("faltan instancias; ejecute primero: bateria.py generar", file = sys.stderr)
        return 1

    os.makedirs(DIR_RESULTADOS, exist_ok = True)
    inicio = time.monotonic()
    total = len(celdas) * len(nombres_agentes)
    hecho = 0
    with open(salida, "w", newline = "") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames = COLUMNAS)
        escritor.writeheader()
        for n, k, m, semilla, ruta in celdas:
            _, _, fichas = cargar_instancia(ruta)
            for nombre in nombres_agentes:
                fila = AGENTES[nombre](n, k, fichas, semilla, limite_seg)
                fila.update(agente = nombre, N = n, K = k, M = m,
                            densidad = round(m / (n * n), 3), semilla = semilla,
                            total_fichas = len(fichas))
                escritor.writerow(fila)
                archivo.flush()
                hecho += 1
                print(f"[{hecho:3d}/{total}] {nombre:10s} N={n:2d} K={k} s={semilla} -> "
                      f"colocadas={fila['colocadas']}/{len(fichas)} ocupadas={fila['ocupadas']} "
                      f"t={fila['tiempo']}s termino={fila['termino']}")
    print(f"\nlisto en {time.monotonic() - inicio:.1f}s -> {os.path.relpath(salida, RAIZ)}")
    return 0

def main(argv = None):
    parser = argparse.ArgumentParser(description = "Bateria de escalabilidad de TileUp")
    sub = parser.add_subparsers(dest = "accion", required = True)
    sub.add_parser("generar", help = "genera las instancias de la rejilla")
    p = sub.add_parser("correr", help = "ejecuta los agentes sobre la rejilla")
    p.add_argument("--agentes", nargs = "+", default = ["evolutivo"],
                   help = f"agentes a ejecutar (disponibles: {', '.join(AGENTES)})")
    p.add_argument("--limite", type = float, default = 10.0, help = "limite de tiempo por corrida, en segundos")
    p.add_argument("--salida", default = os.path.join(DIR_RESULTADOS, "escalabilidad.csv"))
    args = parser.parse_args(argv)

    if args.accion == "generar":
        generar_bateria()
        return 0
    return correr_bateria(args.agentes, args.limite, args.salida)

if __name__ == "__main__":
    sys.exit(main())
