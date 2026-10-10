"""Agente de busqueda por haz (beam search) para TileUp.

Formulacion del problema
------------------------
Estado              Tablero N x N mas el indice de la proxima ficha de la
                    secuencia. Como la secuencia es fija y se consume en orden,
                    todos los nodos de un mismo nivel comparten el indice, de
                    modo que basta el tablero para distinguirlos.
Operador de sucesion Colocar la ficha i en cualquier celda vacia y resolver la
                    fusion. El factor de ramificacion es exactamente la cantidad
                    de celdas vacias.
Costo de la accion  5 - |G|, donde |G| es el tamano de la componente conexa
                    fusionada (1 si no hubo fusion). La ocupacion del tablero
                    varia en 2 - |G| por jugada, de modo que la suma de esas
                    variaciones es exactamente la ocupacion final; sumar 3 a
                    cada arista la vuelve no negativa (rango 0..4) sin alterar
                    el orden entre caminos, porque todos tienen exactamente M
                    aristas. Minimizar el costo acumulado equivale entonces a
                    minimizar las celdas ocupadas al terminar.
Prueba de meta      Haber colocado las M fichas de la secuencia.

Orden del haz y garantia que se pierde
--------------------------------------
Los nodos se ordenan por celdas ocupadas, que en este planteo es el costo
acumulado g y no una estimacion del futuro: el agente es, formalmente, NO
INFORMADO. Se probaron tres heuristicas de anticipacion (celdas cuyo color ya no
reaparece en la secuencia, oportunidades de fusion multiple, y cobertura de los
proximos colores) y ninguna supero a g como predictor del resultado final, por
razones estructurales del juego: casi siempre existe algun lugar donde fusionar,
y las fusiones de mas de dos fichas son muy raras.

Al conservar solo los 'ancho' mejores nodos de cada nivel, el algoritmo deja de
ser completo y optimo: puede descartar el prefijo de la solucion optima sin
posibilidad de recuperarlo. Se renuncia deliberadamente a esa garantia porque el
arbol tiene del orden de 10^126 hojas en las instancias grandes y cualquier
busqueda exhaustiva o con garantia de optimalidad (BFS, costo uniforme, A*) no
entregaria ninguna solucion completa dentro del limite de tiempo.

El ancho es un dial entre dos algoritmos conocidos: con ancho 1 el agente es una
busqueda voraz, y con ancho suficientemente grande nunca se poda y equivale a
BFS exhaustivo.
"""
import os
import sys
import time
from dataclasses import dataclass, replace

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(AQUI)
RAIZ = os.path.dirname(SRC)
for ruta in (SRC,):
    if ruta not in sys.path: sys.path.insert(0, ruta)

from game import createBoard, action
# Se reutilizan del modulo del agente evolutivo para que ambos agentes compartan
# una unica definicion del orden row-major y del formato del archivo de salida.
from agente_evolutivo.agent import Resultado, celdas_vacias, escribir_solucion


@dataclass
class Params:
    ancho_inicial: int = 1       # la primera pasada siempre es barata: garantiza una solucion completa
    factor: int = 4              # cuanto crece el ancho entre pasadas
    ancho_max: int = 8192
    limite_seg: float = 10.0

@dataclass
class Metricas:
    expandidos: int              # medida de esfuerzo: nodos a los que se les generaron sucesores
    generados: int
    ancho: int                   # ancho de la pasada que produjo la mejor solucion
    pasadas: int
    tiempo: float
    motivo_paro: str             # "optimo" | "exhaustivo" | "tiempo" | "ancho_max"


class _Nodo:
    """Nodo del haz. Guarda un puntero al padre en vez de la lista completa de
    colocaciones: reconstruir el camino al final cuesta O(M) una sola vez, en
    lugar de copiar una lista de longitud creciente por cada sucesor."""
    __slots__ = ("tablero", "padre", "celda", "ocupadas", "profundidad")

    def __init__(self, tablero, padre, celda, ocupadas, profundidad):
        self.tablero = tablero
        self.padre = padre
        self.celda = celda
        self.ocupadas = ocupadas
        self.profundidad = profundidad


def _camino(nodo):
    """Reconstruye la lista de colocaciones siguiendo los punteros al padre."""
    celdas = []
    while nodo.celda is not None:
        celdas.append(nodo.celda)
        nodo = nodo.padre
    celdas.reverse()
    return celdas

def _mejor(a, b):
    """Devuelve el mejor de dos nodos segun el orden del enunciado: primero mas
    fichas colocadas, y ante igualdad menos celdas ocupadas."""
    if (a is None): return b
    if (b is None): return a
    return a if (a.profundidad, -a.ocupadas) >= (b.profundidad, -b.ocupadas) else b

def _resultado_de(nodo):
    mayor = max(celda[1] for fila in nodo.tablero for celda in fila)
    colocaciones = _camino(nodo)
    return Resultado(colocaciones = colocaciones, colocadas = len(colocaciones),
                     ocupadas = nodo.ocupadas, mayor = mayor)


def buscar_haz(n, fichas, ancho, vencimiento = None):
    """Una pasada de beam search con ancho fijo.

    Devuelve (mejor_nodo, expandidos, generados, truncado, sin_tiempo).
    'truncado' indica si en algun nivel hubo que podar: si nunca se podo, la
    pasada fue exhaustiva y ampliar el ancho no puede mejorar el resultado.
    """
    haz = [_Nodo(createBoard(n), None, None, 0, 0)]
    mejor = None
    expandidos = generados = 0
    truncado = False

    for ficha in fichas:
        if (vencimiento is not None and time.monotonic() >= vencimiento):
            for nodo in haz: mejor = _mejor(nodo, mejor)
            return mejor, expandidos, generados, truncado, True

        candidatos = []
        vistos = set()
        for indice_nodo, nodo in enumerate(haz):
            # El chequeo por nivel no alcanza: con anchos grandes un nivel puede
            # durar varios segundos, y excederse del limite deja al agente fuera
            # del concurso en esa instancia.
            if (vencimiento is not None and (indice_nodo & 31) == 0
                    and time.monotonic() >= vencimiento):
                for nd in haz: mejor = _mejor(nd, mejor)
                return mejor, expandidos, generados, truncado, True
            vacias = celdas_vacias(nodo.tablero)
            if (not vacias):
                # Tablero lleno con fichas pendientes: este nodo es una derrota.
                mejor = _mejor(nodo, mejor)
                continue
            expandidos += 1
            for celda in vacias:
                tablero = [fila[:] for fila in nodo.tablero]
                action(ficha, celda, tablero)
                generados += 1
                clave = tuple(c for fila in tablero for c in fila)
                if (clave in vistos): continue   # mismo tablero por otro camino
                vistos.add(clave)
                ocupadas = sum(1 for c in clave if c[0] != 0)
                candidatos.append(_Nodo(tablero, nodo, celda, ocupadas, nodo.profundidad + 1))

        if (not candidatos):
            break                                 # todo el haz murio; ya quedo en 'mejor'
        # El orden es estable, asi que los empates en 'ocupadas' se resuelven por
        # orden de generacion (haz previo x celdas en row-major): determinista.
        candidatos.sort(key = lambda nd: nd.ocupadas)
        if (len(candidatos) > ancho): truncado = True
        haz = candidatos[:ancho]

    for nodo in haz: mejor = _mejor(nodo, mejor)
    return mejor, expandidos, generados, truncado, False


def piso_teorico(fichas):
    """Minimo posible de celdas ocupadas: las fusiones solo juntan fichas del
    mismo color, de modo que cada color presente ocupa al menos una celda."""
    return len({color for color, _ in fichas})

def buscar(n, fichas, params):
    """Beam search con ancho creciente, para obtener comportamiento anytime.

    La primera pasada usa ancho 1 y cuesta O(M * N^2), de modo que siempre
    termina y garantiza tener una solucion completa antes de intentar anchos
    mayores. Cada pasada posterior o mejora el resultado o se descarta.
    """
    inicio = time.monotonic()
    vencimiento = inicio + params.limite_seg
    mejor = None
    ancho = max(1, params.ancho_inicial)
    expandidos = generados = pasadas = 0
    ancho_mejor = ancho
    motivo_paro = "ancho_max"
    piso = piso_teorico(fichas)

    while True:
        nodo, exp, gen, truncado, sin_tiempo = buscar_haz(n, fichas, ancho, vencimiento)
        expandidos += exp
        generados += gen
        pasadas += 1
        # Tambien se considera el nodo de una pasada cortada por tiempo: es una
        # solucion parcial valida, y _mejor compara primero por fichas colocadas,
        # de modo que nunca puede desplazar a una solucion completa anterior.
        if (nodo is not None and _mejor(nodo, mejor) is nodo):
            mejor, ancho_mejor = nodo, ancho
        if (mejor is not None and mejor.profundidad == len(fichas) and mejor.ocupadas <= piso):
            # Optimo demostrado: no existe solucion con menos celdas ocupadas.
            # Seguir buscando solo gastaria tiempo, que es el tercer criterio de
            # desempate del concurso.
            motivo_paro = "optimo"
            break
        if (sin_tiempo):
            motivo_paro = "tiempo"
            break
        if (not truncado):
            # El haz nunca se podo: la pasada fue exhaustiva (equivale a BFS) y
            # ningun ancho mayor puede dar un resultado distinto.
            motivo_paro = "exhaustivo"
            break
        if (ancho >= params.ancho_max):
            motivo_paro = "ancho_max"
            break
        if (time.monotonic() >= vencimiento):
            motivo_paro = "tiempo"
            break
        ancho *= params.factor

    metricas = Metricas(expandidos = expandidos, generados = generados, ancho = ancho_mejor,
                        pasadas = pasadas, tiempo = time.monotonic() - inicio,
                        motivo_paro = motivo_paro)
    return mejor, metricas


def informar_metricas(resultado, metricas):
    """Informa por salida estandar lo que pide el requisito 6 del enunciado."""
    print(f"colocadas={resultado.colocadas}")
    print(f"ocupadas={resultado.ocupadas}")
    print(f"mayor={resultado.mayor}")
    print(f"tiempo={metricas.tiempo:.3f}")
    print(f"expandidos={metricas.expandidos}")
    print(f"generados={metricas.generados}")
    print(f"ancho={metricas.ancho}")
    print(f"motivo_paro={metricas.motivo_paro}")


def resolver(n, k, fichas, rng, limite_seg, path_salida = None, params = None):
    """Punto de entrada del agente de busqueda.

    Comparte la firma con el agente evolutivo para que el CLI los intercambie.
    'k' y 'rng' no se usan: el agente no necesita conocer la cantidad de colores
    y es completamente determinista, de modo que la semilla no altera su salida.
    """
    if (params is None): params = Params()
    params = replace(params, limite_seg = limite_seg)

    nodo, metricas = buscar(n, fichas, params)
    resultado = _resultado_de(nodo)

    if (path_salida is None):
        path_salida = os.path.join(RAIZ, 'salidas', 'solution.txt')
    escribir_solucion(path_salida, resultado)
    informar_metricas(resultado, metricas)
    return resultado, metricas
