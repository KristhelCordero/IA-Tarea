from game import *

def processSolution(path):
    file=readFile(path)
    solution = []
    summary = ""
    for line in file.splitlines():
        if line.startswith("#"):
            summary = line
            continue
        list = line.split()
        print(list)
        solution.append((list[1], list[2])) # list[0] = índice de la ficha, list[1] = fila, list[2] = columna 
    return solution, summary

def validateSolution(solution, tiles, board):
    actions = 0
    while True:
        print("--------------------")
        printBoard(board)
        if len(tiles) == 0 and len(solution) != 0:
            print("No tiles left, actions in solution left")
            return False, actions, board
        if len(tiles) == 0 or len(solution) == 0:
            break
        if isBoardFull(board):
            print("The board is full. Cannot place any more tiles.")
            break
        tile = tiles.pop(0)
        cell = solution.pop(0)
        [i,j] = cell
        if i<0 or j<0:
            print("i, j < 0")
            return False, actions, board
        if i>=len(board) or j>=len(board):
            print("i, j >= len(board)")
            return False, actions, board
        if not(board[i][j][0] == 0 and board[i][j][1] == 0): # Check if the cell is empty
            print("Celda no vacía")
            return False, actions, board
        
        print(f"Placing tile {tile} at cell {cell}")
        print("--------------------")
        board = action(tile,cell,board)
        actions += 1

    return True, actions, board

def compareSummary(summary, actions, board):

    pass

def main():
    isValid, nk, amount, tiles = isFileValid('..\\entradas\\instancia_01.txt')
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


main()