from game import *

def processSolution(path):
    file=readFile(path)
    solution = []
    summary = ""
    for line in file.splitlines():
        if line.strip().startswith("# colocadas"):
            summary = line
            continue
        list = line.split()
        print(list)
        solution.append((int(list[0]),int(list[1]), int(list[2]))) # list[0] = índice de la ficha, list[1] = fila, list[2] = columna 
    return solution, summary

def validateSolution(solution, tiles, board):
    actions = 0
    while True:
        print("--------------------")
        printBoard(board)

        if len(solution) == 0 and len(tiles) != 0 and not isBoardFull(board):
            print("No actions left, tiles left and board not full")
            return True, actions, board
        if len(tiles) == 0 and len(solution) != 0:
            print("No tiles left, actions in solution left")
            return False, actions, board
        if len(tiles) == 0 or len(solution) == 0:
            break
        if isBoardFull(board):
            print("The board is full. Cannot place any more tiles.")
            break
        
        index, i, j = solution.pop(0)
        if index != actions:
            print(f"Invalid tile index: expected {actions}, got {index}")
            return False, actions, board
        tile = tiles.pop(0)
        cell = (i, j)

        print(f"Placing tile {tile} at cell {cell}")
        
        if i<0 or j<0:
            print("Invalid cell: i, j < 0")
            return False, actions, board
        if i>=len(board) or j>=len(board):
            print("Invalid cell: i, j >= len(board)")
            return False, actions, board
        if not(board[i][j][0] == 0 and board[i][j][1] == 0): # Check if the cell is empty
            print("Celda no vacía, no se puede colocar la ficha")
            return False, actions, board
        
        print("--------------------")
        board = action(tile,cell,board)
        actions += 1
    return True, actions, board

def format(summary):
    summary = summary.split() 
    for i, s in enumerate(summary):
        summary[i] = s.split("=")[-1]
    newSummary = []
    for c in summary:
        if c.isdigit():
            newSummary.append(int(c))
    return newSummary

def compareSummary(summary, actions, board):
    newSummary = format(summary)
    if newSummary[0] != actions:
        print("Actions in summary do not match actions performed")
        return False
    ocupadas = countOccupiedCells(board)
    if newSummary[1] != ocupadas:
        print("Occupied cells in summary do not match occupied cells on board")
        return False
    mayor = max(cell[1] for row in board for cell in row)
    if newSummary[2] != mayor:
        print("Max value in summary does not match max value on board")
        return False
    return True

def main():
    isValid, nk, amount, tiles = isInputFileValid('..\\entradas\\instancia_01.txt')
    if isValid == False:
        print("Invalid file format. Please check the input file.")
        return
    solution, summary = processSolution('..\\salidas\\solution.txt')
    board = createBoard(nk[0])
    isValid, actions, board = validateSolution(solution, tiles, board)
    if not isValid:
        return print("Solution not valid")
    if not compareSummary(summary, actions, board):
        return print("Solution not valid")
    return print("Solution Valid")

def test(files):
    for file in files:
        print(f"Testing file: {file}")
        isValid, nk, amount, tiles = isInputFileValid(f'..\\testEntradas\\{file}')
        if isValid == False:
            print("Invalid file format. Please check the input file.")
            continue
        solution, summary = processSolution(f'..\\testValidator\\{file}')
        board = createBoard(nk[0])
        isValid, actions, board = validateSolution(solution, tiles, board)
        if not isValid:
            print("Solution not valid")
            continue
        print (f"Actions performed: {actions}, Summary: {summary}")
        if not compareSummary(summary, actions, board):
            print("Solution not valid")
            continue
        print("Solution Valid")
    return print("All tests completed.")

# main()

files = [
    "test_01_sin_combinaciones.txt", #Válido
    "test_02_combinacion_simple.txt", #Válido
    "test_03_tablero_lleno.txt",  #Válido
    "test_04_combinacion_multiple.txt", #Válido 
    "test_05_fuera_de_rango.txt", #Invalido
    "test_06_celda_repetida.txt", #Invalido
    "test_07_combinacion_horizontal.txt", #Válido
    "test_08_iguales_no_adyacentes.txt", #Válido
    "test_09_colores_distintos_adyacentes.txt", #Válido
    "test_10_resumen_incorrecto.txt", #Invalido
    "test_11_acciones_sobrantes.txt", #Invalido
    "test_12_coordenada_negativa.txt", #Invalido
    "test_13_indice_incorrecto.txt", #Invalido
    "test_14_solucion_incompleta.txt", #Valido: timeout antes de colocar todas las fichas
]

test(files)


