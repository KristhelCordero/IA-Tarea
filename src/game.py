import random

#Colores for terminal output ------------------------------------
ESC = '\x1b'
colors = [
    "",
    "\033[31m", # Red
    "\033[32m", # Green
    "\033[33m", # Yellow
    "\033[34m", # Blue
    "\033[35m", # Magenta
    "\033[36m", # Cyan
    "\033[37m", # White
    "\033[0m" # Reset
]
# TODO We need to add more colors or something

#---------------------------------------------------------------

def readFile(path):
    with open(path, 'r') as file:
        return file.read()

def isInputFileValid(path):
    try:
        nk, cant, tiles = processFile(path) # nk = (n, k), cant = (cant,), tiles = [(color, value), ...]
        # n = number of rows/columns, k = number of colors, cant = number of tiles, tiles = list of tiles with color and value
    except (OSError, UnicodeError):
        return False
    if nk is None:
        print("Invalid file format. Please check the input file.")
        return False, nk, cant, tiles
    if nk[0] <= 0 or nk[1] <= 0 or cant[0] <= 0:
        print("Invalid values for n, k, or cant. They must be positive integers")
        return False, nk, cant, tiles
    if cant[0] != len(tiles):
        print("The number of tiles does not match the specified count")
        return False, nk, cant, tiles
    if any(color < 1 or color > nk[1] for color, _ in tiles):
        print(f"Invalid color values in tiles. Colors must be between 1 and {nk[1]}")
        return False, nk, cant, tiles
    return True, nk, cant, tiles

def processFile(path):
    records = []
    file = readFile(path)
    for line in file.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        records.append(line.split())

    # Validate the structure of the records before processing
    if len(records) < 2 or len(records[0]) != 2 or len(records[1]) != 1: 
        # Check if there are at least two lines and the first line has two values and the second line has one value
        # n, k = records[0], cant = records[1]
        return None, 0, []
    if any(len(record) != 2 for record in records[2:]): # Check if all subsequent lines have exactly two values
        return None, 0, []

    try:
        nk = tuple(int(value) for value in records[0])
        cant = (int(records[1][0]),)
        tiles = [tuple(int(value) for value in record) for record in records[2:]]
    except ValueError:
        return None, 0, []

    if cant[0] != len(tiles):
        return None, 0, []

    return nk, cant, tiles

def countOccupiedCells(board):
    count = 0
    for row in board:
        for cell in row:
            if cell[0] != 0 or cell[1] != 0: # Check if the cell is occupied
                count += 1
    return count

def writeSolution(path, solution, board):
    index = 0
    with open(path, 'w') as file:
        for line in solution:
            file.write(f"{index} {line[0]} {line[1]}\n")
            index += 1
        colocadas = len(solution)
        ocupadas = countOccupiedCells(board)
        mayor = max(cell[1] for row in board for cell in row)
        file.write(f"# colocadas = {colocadas} ocupadas = {ocupadas} mayor = {mayor} \n")

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
    [i,j] = cell
    
    neighbors = []

    if i > 0 and board[i-1][j][0] != 0 and board[i-1][j][0] == board[i][j][0]: # Check above color
        neighbors.append((i-1, j))
    if i < len(board)-1 and board[i+1][j][0] != 0 and board[i+1][j][0] == board[i][j][0]: # Check below color
        neighbors.append((i+1, j))
    if j > 0 and board[i][j-1][0] != 0 and board[i][j-1][0] == board[i][j][0]: # Check left color
        neighbors.append((i, j-1))
    if j < len(board[i])-1 and board[i][j+1][0] != 0 and board[i][j+1][0] == board[i][j][0]: # Check right color
        neighbors.append((i, j+1))
    
    if len(neighbors) > 0: #Si se aumenta este número, no se combinan bien los tiles, se tendría que cambiar la lógica de combinación
        # Combine tiles
        combine(neighbors, cell, board)
    return board

def action(tile, cell, board):
    [i,j] = cell
    board[i][j] = tile # Place the tile in the selected cell
    evaluateNeighbors(board, cell) # Evaluate neighbors to check for combinations
    return board

def isWin(tiles):
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
    isValid, nk, amount, tiles = isInputFileValid('..\\entradas\\instancia_01.txt')
    if isValid == False:
        print("Invalid file format. Please check the input file.")
        return
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
    writeSolution("..\\salidas\\solution.txt", solution, board)
    if (isWin(tiles)):
        print("You win!")
        return 100
    print("You lose!")
    return 0

if __name__ == "__main__":
    main()
