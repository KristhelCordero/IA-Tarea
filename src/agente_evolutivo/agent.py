import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from game import createBoard

n = 5
cromo_prueba = [5, 0, 4, 3, 1]
fichas = [(1,2), (4,2), (1,4), (6,9), (3,2)]

class Individuo:
    cromosoma: list[int]
    aptitud: int


def decodificar(cromosoma, n, fichas):
    tablero = createBoard(5)
    print(tablero)

decodificar()