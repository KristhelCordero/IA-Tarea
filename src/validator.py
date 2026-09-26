from game import *

def processSolution(path):
    file=readFile(path)
    solution = []
    for line in file.splitlines():
        list = line.split()
        solution.append((list[1], list[2])) # list[0] = índice de la ficha, list[1] = fila, list[2] = columna 
    return solution

def validateSolution(solution, tiles, board):
    while True:
        print("--------------------")
        printBoard(board)
        if len(tiles) == 0 or len(solution) == 0:
            break
        if isBoardFull(board):
            print("The board is full. Cannot place any more tiles.")
            break
        tile = tiles.pop(0)
        cell = solution.pop(0)
        [i,j] = cell
        if not(board[i][j][0] == 0 and board[i][j][1] == 0): # Check if the cell is empty
            return False
        print(f"Placing tile {tile} at cell {cell}")
        print("--------------------")
    if (isWin(tiles)):
        print("You win!")
        return 100
    print("You lose!")
    return 0

def main():
    isValid, nk, amount, tiles = isFileValid('..\\entradas\\instancia_01.txt')
    if isValid == False:
        print("Invalid file format. Please check the input file.")
        return
    solution = processSolution('..\\salidas\\solution.txt')
    board = createBoard(nk[0])
    validateSolution(solution, tiles, board)
    
    return

    