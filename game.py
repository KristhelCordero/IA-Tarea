import random

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

def processFile(path):
    content = readFile(path)
    tiles = []
    for line in content.splitlines():
        if line.startswith('#') or line.strip() == '':
            continue
        else:
            if line[2:].strip() != '':
                tiles.append((int(line[0]), int(line[2:].strip())))
            else:
                tiles.append((int(line[0]), 0))
    return tiles[0], tiles[1], tiles[2:]

def createBoard(n):
    board = [[(0,0) for _ in range(n)] for _ in range(n)]
    return board

def printBoard(board):
    for row in board:
        for cell in row:
            if cell[0] == 0:
                print(f"{colors[-1]}{cell[1]}{colors[-1]}", end=' ')
            else:           
                print(f"{colors[cell[0]]}{cell[1]}{colors[-1]}", end=' ')
        print(' ')
    return

def action(tile, cell, board):
    for i in range(len(board)):
        for j in range(len(board[i])):
            if [i,j] == cell:
                board[i][j] = tile
    return board

def main():
    nk, length, tiles = processFile('instancia_01.txt')
    board=createBoard(nk[0])
    while True:
        print("--------------------")
        printBoard(board)
        if len(tiles) == 0:
            break
        tile = tiles.pop(0)
        i = random.randint(0, 3)
        j = random.randint(0, 3)
        cell = [i,j]
        board = action(tile, cell, board)


main()
