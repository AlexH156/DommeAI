import pygame
from pygame.locals import *
import random

# initialisation de la surface Pygame
pygame.init()

# nom/FPS de la fenetre définis
fpsClock = pygame.time.Clock()
pygame.display.set_caption('Snake.io')
mySurface = pygame.display.set_mode((1000, 1000))

# COLOR
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# coordonnées
j1 = (1,7)
j2 = (2,8)
j3 = (3,9)
j4 = (4,10)
j5 = (5,11)
j6 = (6,12)

# Images
image_Cell_1 = pygame.image.load("IMAGES/cell_1.bmp")
image_Cell_2 = pygame.image.load("IMAGES/cell_2.bmp")
image_Cell_3 = pygame.image.load("IMAGES/cell_3.bmp")
image_Cell_4 = pygame.image.load("IMAGES/cell_4.bmp")
image_Cell_5 = pygame.image.load("IMAGES/cell_5.bmp")
image_Cell_6 = pygame.image.load("IMAGES/cell_6.bmp")
image_vide = pygame.image.load("IMAGES/vide.bmp")
game_over = pygame.image.load("IMAGES/game_over.jpg")
spacebar = pygame.image.load("IMAGES/start.png")
player1win = pygame.image.load("IMAGES/player1win.png")
player2win = pygame.image.load("IMAGES/player2win.png")
player3win = pygame.image.load("IMAGES/player3win.png")
player4win = pygame.image.load("IMAGES/player4win.png")
player5win = pygame.image.load("IMAGES/player5win.png")
player6win = pygame.image.load("IMAGES/player6win.png")

zqsd = pygame.image.load("IMAGES/zqsd.jpg")
fleches = pygame.image.load("IMAGES/fleches.jpg")

def initBoard():
    tps = 0
    hitj1 = False
    hitj2 = False
    hitj3 = False
    hitj4 = False
    hitj5 = False
    hitj6 = False
    FPS = 20
    dirj1 = random.choice(['up', 'down', 'left', 'right'])
    dirj2 = random.choice(['up', 'down', 'left', 'right'])
    dirj3 = random.choice(['up', 'down', 'left', 'right'])
    dirj4 = random.choice(['up', 'down', 'left', 'right'])
    dirj5 = random.choice(['up', 'down', 'left', 'right'])
    dirj6 = random.choice(['up', 'down', 'left', 'right'])
    breite = random.randrange(40,100,1)
    hoehe = random.randrange(40,100,1)
    board = [[0] * breite for i in range(hoehe)]
    #print(board[79][89])    #len(board) = 80, len(board[1] = 90
    #print(len(board))
    board[random.randrange(0, len(board)-1, 1)][random.randrange(0, len(board[1])-1, 1)] = 1  # Startposition Spieler1
    board[random.randrange(0, len(board)-1, 1)][random.randrange(0, len(board[1])-1, 1)] = 2  # Startposition Spieler2
    board[random.randrange(0, len(board)-1, 1)][random.randrange(0, len(board[1])-1, 1)] = 3  # Startposition Spieler3
    board[random.randrange(0, len(board)-1, 1)][random.randrange(0, len(board[1])-1, 1)] = 4  # Startposition Spieler4
    board[random.randrange(0, len(board)-1, 1)][random.randrange(0, len(board[1])-1, 1)] = 5  # Startposition Spieler5
    board[random.randrange(0, len(board)-1, 1)][random.randrange(0, len(board[1])-1, 1)] = 6  # Startposition Spieler6

    return board, hitj1, hitj2, hitj3, hitj4, hitj5, hitj6, dirj1, dirj2, dirj3, dirj4, dirj5, dirj6, FPS, tps, breite, hoehe


def drawBoard(mySurface, board):
    for j in range(len(board)):
        for i in range(len(board[1])):
            cell = board[j][i]
            if cell == 0:
                draw_vide(mySurface, board, i, j)
            elif cell == 1 or cell == 7:
                draw_Cell_1(mySurface, board, i, j)
            elif cell == 2 or cell == 8:
                draw_Cell_2(mySurface, board, i, j)
            elif cell == 3 or cell == 9:
                draw_Cell_3(mySurface, board, i, j)
            elif cell == 4 or cell == 10:
                draw_Cell_4(mySurface, board, i, j)
            elif cell == 5 or cell == 11:
                draw_Cell_5(mySurface, board, i, j)
            elif cell == 6 or cell == 12:
                draw_Cell_6(mySurface, board, i, j)


def draw_vide(mySurface, board, x, y):
    mySurface.blit(image_vide, (x * 10, y * 10))

def draw_Cell_1(mySurface, board, x, y):
    mySurface.blit(image_Cell_1, (x * 10, y * 10))

def draw_Cell_2(mySurface, board, x, y):
    mySurface.blit(image_Cell_2, (x * 10, y * 10))

def draw_Cell_3(mySurface, board, x, y):
    mySurface.blit(image_Cell_3, (x * 10, y * 10))

def draw_Cell_4(mySurface, board, x, y):
    mySurface.blit(image_Cell_4, (x * 10, y * 10))

def draw_Cell_5(mySurface, board, x, y):
    mySurface.blit(image_Cell_5, (x * 10, y * 10))

def draw_Cell_6(mySurface, board, x, y):
    mySurface.blit(image_Cell_6, (x * 10, y * 10))


def findHead(joueur):
    for i in range(len(board)):
        for j in range(len(board[1])):
            if board[i][j] == joueur[0]:
                return i, j


def moveOn(dir, board, joueur):
    x_head, y_head = findHead(joueur)
    if dir == 'up':
        if (board[x_head - 1][y_head] != 0) or x_head == 0:
            collide(joueur)
        board[x_head][y_head] = joueur[1]
        board[x_head-1][y_head] = joueur[0]
    if dir == 'down':
        if (board[x_head + 1][y_head] != 0) or x_head == (len(board) - 2):
            collide(joueur)
        board[x_head][y_head] = joueur[1]
        board[x_head+1][y_head] = joueur[0]
    if dir == 'left':
        if (board[x_head][y_head - 1] != 0) or y_head == 0:
            collide(joueur)
        board[x_head][y_head] = joueur[1]
        board[x_head][y_head-1] = joueur[0]
    if dir == 'right':
        if (board[x_head][y_head + 1] != 0) or y_head == (len(board[1]) - 2):
            collide(joueur)
        board[x_head][y_head] = joueur[1]
        board[x_head][y_head+1] = joueur[0]
    return board


def collide(joueur):
    global hitj1, hitj2, hitj3, hitj4, hitj5, hitj6
    if joueur[0] == 1:
        hitj1 = True
    elif joueur[0] == 2:
        hitj2 = True
    elif joueur[0] == 3:
        hitj3 = True
    elif joueur[0] == 4:
        hitj4 = True
    elif joueur[0] == 5:
        hitj5 = True
    elif joueur[0] == 6:
        hitj6 = True
    return board


# boucle de jeu
Snake = True
ende = False
board, hitj1, hitj2, hitj3, hitj4, hitj5, hitj6, dirj1, dirj2, dirj3, dirj4, dirj5, dirj6, FPS, tps, breite, hoehe = initBoard()

while Snake:
    # gestion des events
    for event in pygame.event.get():
        if event.type == QUIT:
            Snake = False
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                Snake = False
            if event.key == K_UP:
                if dirj1 != 'down':
                    dirj1 = 'up'
            if event.key == K_DOWN:
                if dirj1 != 'up':
                    dirj1 = 'down'
            if event.key == K_LEFT:
                if dirj1 != 'right':
                    dirj1 = 'left'
            if event.key == K_RIGHT:
                if dirj1 != 'left':
                    dirj1 = 'right'
            if event.key == K_w:
                if dirj2 != 'down':
                    dirj2 = 'up'
            if event.key == K_s:
                if dirj2 != 'up':
                    dirj2 = 'down'
            if event.key == K_a:
                if dirj2 != 'right':
                    dirj2 = 'left'
            if event.key == K_d:
                if dirj2 != 'left':
                    dirj2 = 'right'
            if event.key == K_SPACE:
                if hitj1 or hitj2 or hitj4 or hitj3 or hitj6 or hitj5:
                    ende = False
                    board, hitj1, hitj2, hitj3, hitj4, hitj5, hitj6, dirj1, dirj2, dirj3, dirj4, dirj5, dirj6, FPS, tps, breite, hoehe = initBoard()
    # affichage
    drawBoard(mySurface, board)
    if not hitj1 and not ende:
        board = moveOn(dirj1, board, j1)
    if not hitj2 and not ende:
        board = moveOn(dirj2, board, j2)
    if not hitj3 and not ende:
        board = moveOn(dirj3, board, j3)
    if not hitj4 and not ende:
        board = moveOn(dirj4, board, j4)
    if not hitj5 and not ende:
        board = moveOn(dirj5, board, j5)
    if not hitj6 and not ende:
        board = moveOn(dirj6, board, j6)


    if hitj1 and hitj2 and hitj3 and hitj4 and hitj5 or hitj1 and hitj2 and hitj3 and hitj4 and hitj6 or hitj1 and hitj2 and hitj3 and hitj6 and hitj5 or hitj1 and hitj2 and hitj6 and hitj4 and hitj5 or hitj1 and hitj6 and hitj3 and hitj4 and hitj5 or hitj6 and hitj2 and hitj3 and hitj4 and hitj5:
        mySurface.blit(game_over, (280, 200))
        mySurface.blit(spacebar, (300, 600))
        ende = True
    if hitj1 and hitj2 and hitj3 and hitj4 and hitj5:
        mySurface.blit(player6win, (400, 100))
    if hitj1 and hitj2 and hitj3 and hitj4 and hitj6:
        mySurface.blit(player5win, (400, 100))
    if hitj1 and hitj2 and hitj3 and hitj6 and hitj5:
        mySurface.blit(player4win, (400, 100))
    if hitj1 and hitj2 and hitj6 and hitj4 and hitj5:
        mySurface.blit(player3win, (400, 100))
    if hitj1 and hitj6 and hitj3 and hitj4 and hitj5:
        mySurface.blit(player2win, (400, 100))
    if hitj6 and hitj2 and hitj3 and hitj4 and hitj5:
        mySurface.blit(player1win, (400, 100))
    if tps < 20:
        mySurface.blit(fleches, (650, 750))
        mySurface.blit(zqsd, (250, 150))
        tps += 1

    # rafraichissement de la surface
    pygame.display.update()
    fpsClock.tick(FPS)
pygame.quit()
