import src.agent
import random

# TODO include score calculation for the agent to use in the genetic algorithm functions

#Colores for terminal output ------------------------------------
ESC = '\x1b'
colors = [
    "\033[31m", # Red
    "\033[32m", # Green
    "\033[33m", # Yellow
    "\033[34m", # Blue
    "\033[35m", # Magenta
    "\033[36m", # Cyan
    "\033[37m", # White
    "\033[0m" # Reset
]

#---------------------------------------------------------------

def readFile(path):
    with open(path, 'r') as file:
        return file.read()

def validateFile(path):
    # Implement validation logic to ensure the file format is correct
    # For example, check if the first line contains two integers (n and k)
    # and subsequent lines contain valid tile definitions
    pass

def writeSolution(path, solution, board):
    index = 0
    with open(path, 'w') as file:
        for line in solution:
            file.write(f"{index} {line[0]} {line[1]}\n")
            index += 1
        colocadas = len(solution)
        ocupadas = sum(1 for row in board for cell in row if cell[0] != 0)
        mayor = max(cell[1] for row in board for cell in row)
        file.write(f"# colocadas = {colocadas} ocupadas = {ocupadas} mayor = {mayor} \n")


def processFile(path):
    # Read the file and process its content to extract the board size, length, and tiles
    # TODO: Include validation to ensure the file format is correct and handle any potential errors
    # validateFile(path)
    content = readFile(path)
    tiles = []
    for line in content.splitlines():
        if line.startswith('#') or line.strip() == '':
            continue
        else:
            if line[2:].strip() != '':
                tiles.append((int(line[0]), int(line[2:].strip()))) # (Color, value), that's the order of the tiles in the file
            else:
                tiles.append((int(line[0]), 0)) 
    return tiles[0], tiles[1], tiles[2:] # Return nk, cant tiles, and tiles list

def createBoard(n):
    board = [[(0,0) for _ in range(n)] for _ in range(n)]
    return board

def printBoard(board):
    for row in board:
        for cell in row:
            if cell[0] == 0:
                print(f"{colors[-1]}{cell[1]}{colors[-1]}", end=' ') # Print empty cell with default color
            else:           
                print(f"{colors[cell[0]]}{cell[1]}{colors[-1]}", end=' ') # Print cell with its color and value
        print(' ')
    return

def combine(neighboors, selected, board):
    #combinar los 3 tiles en uno solo, sumando el valor de cada una
    suma = 0
    for neighbor in neighboors:
        suma += board[neighbor[0]][neighbor[1]][1]
        board[neighbor[0]][neighbor[1]] = (0, 0)  # Clear the neighbor cell
    [i, j] = selected
    suma += board[i][j][1]
    color = board[i][j][0]
    board[i][j] = (color, suma)  # Update the selected cell with the combined value
    return 

def evaluateNeighbors(board, cell):
    #revisar si hay 2 o más vecinos con el mismo color, si es así combinar en una sola celda sumando el valor de todasy vaciar las otras
    for i in range(len(board)):
        for j in range(len(board[i])):
            if [i,j] == cell:
                # Check neighbors
                neighbors = []
                if i > 0 and board[i-1][j][0] == board[i][j][0]: # Check above color
                    neighbors.append((i-1, j))
                if i < len(board)-1 and board[i+1][j][0] == board[i][j][0]: # Check below color
                    neighbors.append((i+1, j))
                if j > 0 and board[i][j-1][0] == board[i][j][0]: # Check left color
                    neighbors.append((i, j-1))
                if j < len(board[i])-1 and board[i][j+1][0] == board[i][j][0]: # Check right color
                    neighbors.append((i, j+1))
                
                if len(neighbors) >= 2:
                    # Combine tiles
                    combine(neighbors, cell, board)
    return board

def action(tile, cell, board):
    for i in range(len(board)):
        for j in range(len(board[i])):
            if [i,j] == cell:
                board[i][j] = tile # Place the tile in the selected cell
    evaluateNeighbors(board, cell) # Evaluate neighbors to check for combinations
    return board

def isWin(tiles):
    # TODO: La partida termina con victoria cuando se colocan las M fichas de la secuencia. Termina con derrota cuando
    # queda al menos una ficha pendiente y el tablero no tiene ninguna celda vacía.
    if tiles == []:
        return True # Win condition: all tiles placed
    return False # Not win condition: tiles still remaining

def isBoardFull(board):
    for row in board:
        for cell in row:
            if cell[0] == 0 and cell[1] == 0: # Check if the cell is empty
                return False
    return True

def main():
    nk, amount, tiles = processFile('instancia_01.txt')
    board=createBoard(nk[0])
    solution=[]
    while True:
        print("--------------------")
        printBoard(board)
        if len(tiles) == 0:
            break
        if isBoardFull(board):
            print("The board is full. Cannot place any more tiles.")
            break
        tile = tiles.pop(0)
        while True: # Ensure the selected cell is empty
            i = random.randint(0, 3)
            j = random.randint(0, 3)
            cell = [i,j]
            if board[i][j][0] == 0 and board[i][j][1] == 0: # Check if the cell is empty
                break
        
        print(f"Placing tile {tile} at cell {cell}")
        solution.append(cell)
        board = action(tile, cell, board)
    if (isWin(tiles)):
        print("You win!")
    else:
        print("You lose!")
    writeSolution("solution.txt", solution, board)

main()
