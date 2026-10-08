"""Generador de instancias de TileUp parametrizado por N, K, M y semilla.

Uso:
    python3 src/generador.py <N> <K> <M> <semilla> [salida]

La misma semilla produce siempre la misma instancia, para que los experimentos
sean reproducibles.
"""
import random
import sys

VALOR_MAX = 4   # rango de valores de ficha, consistente con las instancias dadas

def generar(n, k, m, semilla):
    """Devuelve la lista de m fichas (color, valor) de la instancia."""
    rng = random.Random(semilla)
    return [(rng.randint(1, k), rng.randint(1, VALOR_MAX)) for _ in range(m)]

def escribir(path, n, k, fichas, comentario = ""):
    with open(path, 'w') as archivo:
        archivo.write(f"# TileUp -- {comentario}\n")
        archivo.write(f"{n} {k}\n")
        archivo.write(f"{len(fichas)}\n")
        for color, valor in fichas:
            archivo.write(f"{color} {valor}\n")

def main():
    if (len(sys.argv) < 5):
        print("uso: python3 src/generador.py <N> <K> <M> <semilla> [salida]", file = sys.stderr)
        return 1
    n, k, m, semilla = (int(a) for a in sys.argv[1:5])
    if (n <= 0 or k <= 0 or m <= 0):
        print("N, K y M deben ser positivos", file = sys.stderr)
        return 1
    salida = sys.argv[5] if len(sys.argv) > 5 else f"entradas/instancia_N{n}_K{k}_M{m}_s{semilla}.txt"
    fichas = generar(n, k, m, semilla)
    escribir(salida, n, k, fichas, f"generada con N={n} K={k} M={m} semilla={semilla}")
    print(f"escrita en {salida}  (densidad {m/(n*n):.2f})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
