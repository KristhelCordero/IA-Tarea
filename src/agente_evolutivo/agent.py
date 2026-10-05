import sys
import os
from dataclasses import dataclass
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from game import createBoard, action

n = 5
cromo_prueba = [5, 0, 4, 3, 1]
fichas = [(1,2), (4,2), (1,4), (6,9), (3,2)]

@dataclass
class Individuo:
    cromosoma: list[int]
    aptitud: int

@dataclass
class Resultado:
    colocaciones: list[tuple[int, int]]  # (fila, col) por ficha, en orden
    colocadas: int                       # == len(colocaciones)
    ocupadas: int
    mayor: int

def celdas_vacias(tablero):
    """Celdas libres del tablero, en orden row-major (por fila, luego por columna).

    El orden es canónico y determinista: la decodificación indexa sobre esta
    lista, así que si el orden variara entre ejecuciones el agente dejaría de
    ser reproducible con la misma semilla.
    """
    return [(i, j)
            for i, fila in enumerate(tablero)
            for j, celda in enumerate(fila)
            if celda[0] == 0]

def decodificar(cromosoma, n, fichas):
    tablero = createBoard(n)
    colocaciones = []
    for i, ficha in enumerate(fichas):
        vacias = celdas_vacias(tablero)
        # Verificar si vacias esta vacia, si es asi, entonces perdimos
        if (len(vacias) == 0): break
        elegida = vacias[cromosoma[i] % len(vacias)]
        tablero = action(ficha, elegida, tablero)
        colocaciones.append(elegida)
    
    ocupadas = sum(1 for row in tablero for cell in row if cell[0] != 0)
    mayor = max(cell[1] for row in tablero for cell in row)

    return Resultado(colocaciones = colocaciones, colocadas = len(colocaciones), ocupadas = ocupadas, mayor = mayor)

def aptitud(resultado, n):
    return resultado.colocadas * (n*n + 1) - resultado.ocupadas

def crear_cromosoma(rng, m, n):
    cromosoma = []
    for _ in range(m):
        cromosoma.append(rng.randint(0, n*n - 1))
    return cromosoma

def busqueda_aleatoria(n, fichas, rng, num_muestras):
    if (num_muestras <= 0): return None
    individuos = []
    for _ in range(num_muestras):
        cromosoma = crear_cromosoma(rng, len(fichas), n)
        apt = aptitud(decodificar(cromosoma, n, fichas), n)
        individuos.append(Individuo(cromosoma = cromosoma, aptitud = apt))
    return max(individuos, key=lambda i: i.aptitud)
