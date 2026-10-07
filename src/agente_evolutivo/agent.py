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

def crear_poblacion_inicial(rng, tam_poblacion, n, fichas):
    if (tam_poblacion <= 0): return None
    poblacion = []
    for _ in range(tam_poblacion):
        cromosoma = crear_cromosoma(rng, len(fichas), n)
        apt = aptitud(decodificar(cromosoma, n, fichas), n)
        poblacion.append(Individuo(cromosoma = cromosoma, aptitud = apt))
    return poblacion

def seleccion_torneo(poblacion, k, rng):
    # Seleccion con reemplazo de la poblacion
    indices = []
    seleccionados = []
    for _ in range(k):
        indices.append(rng.randint(0, len(poblacion) - 1))
    for i in indices:
        seleccionados.append(poblacion[i])
    return max(seleccionados, key=lambda i: i.aptitud)

def cruce_un_punto(cromosoma_padre1, cromosoma_padre2, rng):
    punto_corte = rng.randint(1, len(cromosoma_padre1) - 1)
    return (cromosoma_padre1[:punto_corte]+cromosoma_padre2[punto_corte:], cromosoma_padre2[:punto_corte]+cromosoma_padre1[punto_corte:])

def mutacion(cromosoma, tasa, n, rng):
    copia_cromosoma = list(cromosoma)
    for i, gen in enumerate(copia_cromosoma):
        if (rng.random() < tasa):
            copia_cromosoma[i] = rng.randint(0, n*n - 1)
    return copia_cromosoma

def reemplazo(poblacion, hijos, tam_elite):
    poblacion.sort(key=lambda i: i.aptitud, reverse=True)
    reemplazo = poblacion[:tam_elite] + hijos
    if (len(reemplazo) > len(poblacion)): reemplazo = reemplazo[:len(poblacion)]
    return reemplazo

def evolucionar(n, fichas, rng, params):
    poblacion = crear_poblacion_inicial(rng, params.tam_poblacion, n, fichas)
    mejor = max(poblacion, key=lambda i: i.aptitud)
    sin_mejora = 0
    while True:
        hijos = []
        while (len(hijos) < len(poblacion) - params.tam_elite):
            padre1 = seleccion_torneo(poblacion, params.k, rng)
            padre2 = seleccion_torneo(poblacion, params.k, rng)
            if (rng.random() < params.prob_cruce):
                cromo1, cromo2 = cruce_un_punto(padre1.cromosoma, padre2.cromosoma, rng)
            else:
                cromo1 = padre1.cromosoma
                cromo2 = padre2.cromosoma
            cromo1 = mutacion(cromo1, params.tasa, n, rng)
            cromo2 = mutacion(cromo2, params.tasa, n, rng)
            # Obtener la aptitud
            hijos.append(Individuo(cromosoma = cromo1, aptitud = aptitud(decodificar(cromo1, n, fichas), n)))
            hijos.append(Individuo(cromosoma = cromo2, aptitud = aptitud(decodificar(cromo2, n, fichas), n)))
        poblacion = reemplazo(poblacion, hijos, params.tam_elite)
        nuevo_mejor = max(poblacion, key=lambda i: i.aptitud)
        if (nuevo_mejor.aptitud > mejor.aptitud):
            mejor = nuevo_mejor
            sin_mejora = 0
        else:
            sin_mejora += 1
        # Definir condicion de parada
    
    return mejor