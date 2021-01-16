#!/usr/bin/env python3

import asyncio
import random
import time
from datetime import datetime
import json
from queue import Queue

import numpy as np
from matplotlib import pyplot, colors
import dateutil.parser as dp
import websockets

# TODO alles aufhübschen (keine Prio)
# TODO evtl: teilweise berechnete Ebenen mit Durchschnitt berechnen lassen (keine Prio)
# TODO Evtl zweite Tiefe der Gegner mit einbinden (wenn bestimmte Nähe)


global logActionValue
global q
global queueDepth

global checkD  # Debugging





# Gets the current directions its headed and the change (left or right). Returns the new direction
def getnewdirection(direction, change):
    if direction == change:
        return "down"
    if change == "left":
        if direction == "up":
            return "left"
        elif direction == "down":
            return "right"
        else:
            return "up"
    else:
        if direction == "down":
            return "left"
        elif direction == "up":
            return "right"
        else:
            return "up"


# Gets the curent x and y-position, as well as speed and direction to determine the new head-position in the next step
def getnewpos(x, y, speed, direction):
    if direction == "up":
        return y - speed, x
    elif direction == "down":
        return y + speed, x
    elif direction == "left":
        return y, x - speed
    else:
        return y, x + speed


def checkFront(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord, distance,
               collCounter, checkCounter, sackG):
    # checkCounter: +1 wenn rechts oder links, +0 wenn vorne
    newaction = action
    init = action is None
    coordIgnore = checkCounter < 3  # True, wenn Koordinaten nicht geprüft werden müssen
    isJumping = counter % 6 == 0
    newcoord = coord[:]

    # Vorgehen: Bei Sprung prüfe erst gemeinsamen Schwanz, dann jeweils Kopf
    if isJumping:
        newbodyY, newbodyX = getnewpos(x, y, 1, direction)
        if height > newbodyY >= 0 and width > newbodyX >= 0 and board[newbodyY][newbodyX] == 0 and (
                coordIgnore or [newbodyY, newbodyX] not in coord):
            newcoord.append([newbodyY, newbodyX])
            skip = speed == 2   # SD doesn't have to be checked again if speed==2
            # Slow-Down
            newheadY, newheadX = getnewpos(x, y, speed - 1, direction)
            if skip or (speed > 1 and height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    coordIgnore or [newheadY, newheadX] not in coord)):
                newcoord0 = newcoord[:]
                if speed > 2:
                    newcoord0.append([newheadY, newheadX])
                if init:
                    newaction = 1
                logActionValue[depth][newaction] += wert
                if sackG and logActionValue[0][newaction] == 1 and overSnake(x, y, board, direction, speed - 1) and not deadend(
                        newheadX, newheadY, board, direction, width, height) < 14:
                    logActionValue[0][newaction] = 500
                q.put((checkchoices, [newheadX, newheadY, direction, board, speed - 1, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, newaction, newcoord0, distance, 0, checkCounter,
                                      sackG]))
            # Change-Nothing
            newheadY, newheadX = getnewpos(x, y, speed, direction)
            if height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    coordIgnore or [newheadY, newheadX] not in coord):
                newcoord1 = newcoord[:]
                if speed > 1:
                    newcoord1.append([newheadY, newheadX])
                if init:
                    newaction = 2
                logActionValue[depth][newaction] += wert
                if sackG and logActionValue[0][newaction] == 1 and overSnake(x, y, board, direction, speed) and not deadend(
                        newheadX, newheadY, board, direction, width, height) < 14:
                    logActionValue[0][newaction] = 500
                q.put((checkchoices, [newheadX, newheadY, direction, board, speed, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, newaction, newcoord1, distance, 0, checkCounter,
                                      sackG]))
            # Speed-Up
            newheadY, newheadX = getnewpos(x, y, speed + 1, direction)
            if speed < 10 and height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    coordIgnore or [newheadY, newheadX] not in coord):
                newcoord2 = newcoord[:]
                newcoord2.append([newheadY, newheadX])
                if init:
                    newaction = 0
                logActionValue[depth][newaction] += wert
                if sackG and logActionValue[0][newaction] == 1 and overSnake(x, y, board, direction, speed + 1) and not deadend(
                        newheadX, newheadY, board, direction, width, height) < 14:
                    logActionValue[0][newaction] = 500
                q.put((checkchoices, [newheadX, newheadY, direction, board, speed + 1, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, newaction, newcoord2, distance, 0, checkCounter,
                                      sackG]))
    # Vorgehen: Bei nicht-Sprung prüfe sd komplett, dann Kopf cn, dann Kopf su
    else:
        newcoord0 = coord[:]
        hit = False
        # Slow-Down
        if speed > 1:
            newheadY, newheadX = getnewpos(x, y, speed - 1, direction)
            if height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    coordIgnore or [newheadY, newheadX] not in coord):
                newcoord0.append([newheadY, newheadX])
                for i in range(1, speed - 1):
                    newbodyY, newbodyX = getnewpos(x, y, i, direction)
                    if board[newbodyY][newbodyX] != 0 or (not coordIgnore and [newbodyY, newbodyX] in coord):
                        hit = True
                        break
                    newcoord0.append([newbodyY, newbodyX])
                if not hit:
                    if init:
                        newaction = 1
                    logActionValue[depth][newaction] += wert
                    q.put((checkchoices, [newheadX, newheadY, direction, board, speed - 1, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, newaction, newcoord0, distance, 0,
                                          checkCounter, sackG]))
            else:
                hit = True
        if not hit:
            # Change-Nothing
            newheadY, newheadX = getnewpos(x, y, speed, direction)
            if height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    coordIgnore or [newheadY, newheadX] not in coord):
                newcoord1 = newcoord0[:]
                newcoord1.append([newheadY, newheadX])
                if init:
                    newaction = 2
                logActionValue[depth][newaction] += wert
                q.put((checkchoices, [newheadX, newheadY, direction, board, speed, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, newaction, newcoord1, distance, 0, checkCounter,
                                      sackG]))
                # Speed-Up
                newheadY, newheadX = getnewpos(x, y, speed + 1, direction)
                if speed < 10 and height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][
                    newheadX] == 0 and (coordIgnore or [newheadY, newheadX] not in coord):
                    newcoord2 = newcoord1[:]
                    newcoord2.append([newheadY, newheadX])
                    if init:
                        newaction = 0
                    logActionValue[depth][newaction] += wert
                    q.put((checkchoices, [newheadX, newheadY, direction, board, speed + 1, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, newaction, newcoord2, distance, 0,
                                          checkCounter, sackG]))


def checkLeftorRight(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                     collCounter, checkCounter, change, distance, sackG):
    # collCounter: +1 wenn rechts, -1 wenn links, =0 wenn vorne
    # collCounter == 2: checkright muss nicht geprüft werden
    # collCounter == -2: checkleft muss nicht geprüft werden
    # checkCounter: +1 wenn rechts oder links, +0 wenn vorne
    coordIgnore = checkCounter < 2  # True, wenn Koordinaten nicht geprüft werden müssen
    direction = getnewdirection(direction, change)
    isJumping = counter % 6 == 0
    newcoord = coord[:]

    newheadY, newheadX = getnewpos(x, y, speed, direction)
    if (change == "left" and collCounter != -2 or change == "right" and collCounter != 2) and height > newheadY >= 0 \
            and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
            coordIgnore or [newheadY, newheadX] not in coord):
        isHit = False
        newcoord.append([newheadY, newheadX])
        for i in range(1, speed):
            if isJumping:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                newbodyY, newbodyX = getnewpos(x, y, 1, direction)
                if board[newbodyY][newbodyX] != 0 or (not coordIgnore and [newbodyY, newbodyX] in coord):
                    isHit = True
                    break
                newcoord.append([newbodyY, newbodyX])
                break
            newbodyY, newbodyX = getnewpos(x, y, i, direction)
            if board[newbodyY][newbodyX] != 0 or (not coordIgnore and [newbodyY, newbodyX] in coord):
                isHit = True
                break
            newcoord.append([newbodyY, newbodyX])
        if not isHit:
            logActionValue[depth][action] += wert
            if isJumping and logActionValue[0][action] == 1 and sackG and overSnake(x, y, board, direction, speed) and not deadend(
                    newheadX, newheadY, board, direction, width, height) < 14:
                logActionValue[0][action] = 500
            if change == "left":
                if not collCounter > 0:
                    checkCounter += 1
                collCounter = min(collCounter - 1, - 1)
            else:
                if not collCounter < 0:
                    checkCounter += 1
                collCounter = max(collCounter + 1, 1)
            q.put((checkdistance, [newheadX, newheadY, direction, board, speed, width, height, wert / 2, depth + 1,
                                   counter + 1, deadline, action, newcoord, distance - speed, collCounter, checkCounter,
                                   sackG]))


# Return a board that has every possible action from active enemies registered
def constructEnemyBoard(state, isJumping):
    enemyBoard = state["cells"]
    # Gehe durch alle Spieler die noch aktiv sind
    for enemy in range(1, len(state["players"]) + 1):
        enemyObject = state["players"][str(enemy)]
        if enemyObject["active"] and not state["you"] == enemy:
            # Prüfe erst ob bei Verlangsamung überleben würde, trage ein, dann CN prüfen und eintragen,
            # als letztes Beschleinigung prüfen und eintragen (Beachte nicht Sonderfall der 6.ten Runde)
            newHeadPosList = []
            currDirection = enemyObject["direction"]
            speedNotTen = 1
            if enemyObject["speed"] % 10 == 0:
                newSpeed = 10
                speedNotTen = 0
            else:
                newSpeed = enemyObject["speed"] + 1

            newHeadPosList.append(getnewpos(enemyObject["x"], enemyObject["y"], newSpeed, currDirection))

            newDirection = getnewdirection(currDirection, "left")
            newHeadPosList.append(getnewpos(enemyObject["x"], enemyObject["y"], enemyObject["speed"], newDirection))

            newDirection = getnewdirection(currDirection, "right")
            newHeadPosList.append(getnewpos(enemyObject["x"], enemyObject["y"], enemyObject["speed"], newDirection))

            if isJumping:
                pathList = []
                pathList.append(np.zeros(newSpeed, dtype=np.int32))
                pathList[0][0] = 7
                pathList[0][-1] = 7
                pathList[0][-2] = 7

                pathList.append(np.zeros(newSpeed - 1 * speedNotTen, dtype=np.int32))
                pathList[1][0] = 7
                pathList[1][-1] = 7

                if newSpeed >= 3:
                    pathList[0][-3] = 7
            else:
                pathList = []
                pathList.append(np.full((newSpeed), 7, dtype=np.int32))
                pathList.append(np.full((newSpeed - 1 * speedNotTen), 7, dtype=np.int32))

            pathNum = 0
            for newHeadPos in newHeadPosList:
                numberSteps = 0
                stepVector = [newHeadPos[0] - enemyObject["y"], newHeadPos[1] - enemyObject["x"]]

                if stepVector[1] == 0:
                    stepVector[0] = stepVector[0] / abs(stepVector[0])
                    boundHelp = (stepVector[0] + 1) * 0.5
                    numberSteps = min(abs(boundHelp * (state["height"] - 1) - enemyObject["y"]),
                                      newSpeed - 1 * pathNum * speedNotTen)
                else:
                    stepVector[1] = stepVector[1] / abs(stepVector[1])
                    boundHelp = (stepVector[1] + 1) * 0.5
                    numberSteps = min(abs(boundHelp * (state["width"] - 1) - enemyObject["x"]),
                                      newSpeed - 1 * pathNum * speedNotTen)

                chosenPath = pathList[pathNum]
                numberSteps = int(numberSteps)
                for step in range(1, numberSteps + 1):
                    stepX = enemyObject["x"] + stepVector[1] * step
                    stepY = enemyObject["y"] + stepVector[0] * step
                    enemyBoard[int(stepY)][int(stepX)] = max(chosenPath[step - 1], enemyBoard[int(stepY)][int(stepX)])
                pathNum = 1
    return enemyBoard


# Return the count of free fields in the given direction
def distanz(x, y, board, direction, width, height):
    dis = 0
    if direction == "up":
        while y > 0 and board[y - 1][x] == 0:
            y -= 1
            dis += 1
    elif direction == "down":
        while y < height - 1 and board[y + 1][x] == 0:
            y += 1
            dis += 1
    elif direction == "right":
        while x < width - 1 and board[y][x + 1] == 0:
            x += 1
            dis += 1
    else:  # left
        while x > 0 and board[y][x - 1] == 0:
            x -= 1
            dis += 1
    return dis


def maxLR(x, y, board, direction, width, height):
    px = x
    py = y
    # print(px, py)

    ld = 0
    if direction == "right":  # checks up  (left of right)
        while py > 0 and board[py - 1][px] == 0:
            py -= 1
            ld += 1
    elif direction == "left":  # checks down
        while py < height - 1 and board[py + 1][px] == 0:
            py += 1
            ld += 1
    elif direction == "down":  # checks right
        while px < width - 1 and board[py][px + 1] == 0:
            px += 1
            ld += 1
    else:  # checks left
        while px > 0 and board[py][px - 1] == 0:
            px -= 1
            ld += 1

    px = x
    py = y
    # print(px, py)

    rd = 0
    if direction == "left":  # checks up (right of left)
        while py > 0 and board[py - 1][px] == 0:
            py -= 1
            rd += 1
    elif direction == "right":  # checks down
        while py < height - 1 and board[py + 1][px] == 0:
            py += 1
            rd += 1
    elif direction == "up":  # checks right
        while px < width - 1 and board[py][px + 1] == 0:
            px += 1
            rd += 1
    else:  # checks left
        while px > 0 and board[py][px - 1] == 0:
            px -= 1
            rd += 1

    return max(ld, rd)


def deadendDir(x, y, board, direction, width, height):
    px = x
    py = y

    dis = 0
    if direction == "up":
        while py > 0 and board[py - 1][px] == 0:
            py -= 1
            dis += 1
    elif direction == "down":
        while py < height - 1 and board[py + 1][px] == 0:
            py += 1
            dis += 1
    elif direction == "right":
        while px < width - 1 and board[py][px + 1] == 0:
            px += 1
            dis += 1
    else:  # left
        while px > 0 and board[py][px - 1] == 0:
            px -= 1
            dis += 1

    LR = maxLR(px, py, board, direction, width, height)

    return dis + LR


def deadend(x, y, board, direction, width, height):
    straight = deadendDir(x, y, board, direction, width, height)
    right = deadendDir(x, y, board, getnewdirection(direction, "right"), width, height)
    left = deadendDir(x, y, board, getnewdirection(direction, "left"), width, height)

    return max(straight, right, left)


# Returns a Boolean-Value if the snake jumped over another one
def overSnake(x, y, board, direction, speed):
    if speed < 3:
        return False
    for i in range(2, speed):
        newy, newx = getnewpos(x, y, i, direction)
        if board[newy][newx] != 0:
            # print("Über Schlange" + str(newy) + " " + str(newx))
            return True
    return False


# GUI
def anzeige(state, counter, action, choices, depth, LR, de, deDir, sackG):
    # Informationen über den aktuellen Stand des eigenen Spielers
    youx = str(state["players"][str(state["you"])]["x"])
    youy = str(state["players"][str(state["you"])]["y"])
    youdir = str(state["players"][str(state["you"])]["direction"])
    youspeed = str(state["players"][str(state["you"])]["speed"])
    for i in range(0, 5):
        choices[i] = round(choices[i], 2)

    board = state["cells"]  # Das Spielfeld als 2D Matrix
    w = max(state["width"] / 10, 5.8)  # Breite des GUI
    h = (state["height"] / 10) + 0.5  # Höhe des GUI

    anzahl = int(len(state["players"]))
    farben = ["grau", "weiß", "grün", "blau", "orange", "rot", "cyan", "magenta"]

    # Köpfe der Schlangen durch "-1" ersetzen, um sie zu visualisieren
    for p in range(1, (anzahl + 1)):
        try:
            board[state["players"][str(p)]["y"]][state["players"][str(p)]["x"]] = -1
        except IndexError:
            pass

    with pyplot.xkcd():  # Stil der xkcd Comics, für normalen Stil einfach auskommentieren
        pyplot.figure(figsize=(w, h))

        # Farben
        if anzahl == 6:
            colormap = colors.ListedColormap(["grey", "white", "green", "blue", "orange", "red", "cyan", "magenta"])
        elif anzahl == 5:
            colormap = colors.ListedColormap(["grey", "white", "green", "blue", "orange", "red", "cyan"])
        elif anzahl == 4:
            colormap = colors.ListedColormap(["grey", "white", "green", "blue", "orange", "red"])
        elif anzahl == 3:
            colormap = colors.ListedColormap(["grey", "white", "green", "blue", "orange"])
        else:
            colormap = colors.ListedColormap(["grey", "white", "green", "blue"])

        pyplot.imshow(board, cmap=colormap)
        pyplot.title("DommeAI: " + farben[(state["you"] + 1)] + "\n" + "Runde: " + str(counter - 1))  # Überschrift
        pyplot.xticks([])  # keine Achsenbeschriftungen
        pyplot.yticks([])  #
        pyplot.xlabel("x: " + youx + " y: " + youy + " | dir: " + youdir + " | speed: " + youspeed + " | LR: " + str(
            LR) + " | DeDir: " + str(deDir) + " | De: " + str(de) +
                      "\n" + str(choices) + " | SG: " + str(sackG) +
                      "\n" + "nächster Zug: " + str(action) + "  |  Tiefe: " + str(depth) + " | Jump in T - " + str(
            5 - ((counter - 2) % 6)))
        pyplot.show(block=False)


# TODO In diesem Szenario leicht anderes Ergebnis
def checkdistance(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                  distance, collCounter, checkCounter, sackG):
    global logActionValue
    global q
    global queueDepth

    global checkD
    checkD += 1  # Debugging

    # Wenn weniger als eine Sekunde bis zur Deadline verbleibt, bearbeite die Queue nicht weiter
    if time.time() + 1 > deadline:
        if myc > 4:  # still to be tested
            return

    if not len(ebene) > depth:
        ebene.append([0, 0, 0, 0, 0])
        myc = depth

    # if distance > speed+1:
    # ebene += ..., etc
    # add to Queue: SU, CN, SD (CheckDistance)
    # board und cd werte jeweils aktualisieren

    # checkleft, checkright

    # ist es in diesem Schritt möglich? -> CC
    # elif distance == speed+1:
    # ebene += ..., etc
    # add to Queue: SU, CN, SD (CheckChoices)
    # board und cc werte jeweils aktualisieren

    # ist es in diesem Zug möglich
    if distance > speed:
        if distance == (speed + 1):
            checkWhat = checkchoices
        else:
            checkWhat = checkdistance

        newaction = action
        init = action is None
        isJumping = counter % 6 == 0

        newcoord = coord[:]

        # ist es evtl im nächsten Schritt möglich? -> CD
        if isJumping:
            newy, newx = getnewpos(x, y, 1, direction)
            newcoord.append([newy, newx])

            # speed_down in queue
            if speed > 1:
                newy, newx = getnewpos(x, y, speed - 1, direction)
                newcoord0 = newcoord[:]
                if speed > 2:
                    newcoord0.append([newy, newx])
                if init:
                    newaction = 1
                ebene[depth][newaction] += wert
                q.put((checkWhat, [newx, newy, direction, board, speed - 1, width, height, wert / 2,
                                   depth + 1, counter + 1, deadline, newaction, newcoord0,
                                   distance - (speed - 1), 0, checkCounter, sackG]))

            # change_nothing
            newy, newx = getnewpos(x, y, speed, direction)
            newcoord1 = newcoord[:]
            newcoord1.append([newy, newx])
            if init:
                newaction = 2
            ebene[depth][newaction] += wert
            q.put((checkWhat, [newx, newy, direction, board, speed, width, height, wert / 2,
                               depth + 1, counter + 1, deadline, newaction, newcoord1, distance - speed, 0,
                               checkCounter, sackG]))
            # speed_up
            if speed < 10:
                newy, newx = getnewpos(x, y, speed + 1, direction)
                newcoord2 = newcoord[:]
                newcoord2.append([newy, newx])
                if init:
                    newaction = 0
                ebene[depth][newaction] += wert
                q.put((checkWhat, [newx, newy, direction, board, speed + 1, width, height, wert / 2,
                                   depth + 1, counter + 1, deadline, newaction, newcoord2,
                                   distance - (speed + 1), 0, checkCounter, sackG]))
        else:
            if speed > 1:
                for i in range(1, speed - 1):
                    newyy, newxx = getnewpos(x, y, i, direction)
                    newcoord.append([newyy, newxx])
                # speed_down
                newy, newx = getnewpos(x, y, speed - 1, direction)
                if speed > 2:
                    newcoord.append([newy, newx])
                if init:
                    newaction = 1
                ebene[depth][newaction] += wert
                q.put((checkWhat, [newx, newy, direction, board, speed - 1, width, height, wert / 2,
                                   depth + 1, counter + 1, deadline, newaction, newcoord,
                                   distance - (speed - 1), 0, checkCounter, sackG]))
            # change_nothing
            newy, newx = getnewpos(x, y, speed, direction)
            newcoord1 = newcoord[:]
            newcoord1.append([newy, newx])
            if init:
                newaction = 2
            ebene[depth][newaction] += wert
            q.put((checkWhat, [newx, newy, direction, board, speed, width, height, wert / 2,
                               depth + 1, counter + 1, deadline, newaction, newcoord1, distance - speed, 0,
                               checkCounter, sackG]))

            # speed_up
            if speed < 10:
                newy, newx = getnewpos(x, y, speed + 1, direction)
                newcoord2 = newcoord1[:]
                newcoord2.append([newy, newx])
                if init:
                    newaction = 0
                ebene[depth][newaction] += wert
                q.put((checkWhat, [newx, newy, direction, board, speed + 1, width, height, wert / 2,
                                   depth + 1, counter + 1, deadline, newaction, newcoord2,
                                   distance - (speed + 1), 0, checkCounter, sackG]))

        # init bedeutet ist erster Aufruf und daher wird LR extra aufgerufen
        if not init:
            # check-left
            checkLeftorRight(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action,
                             coord, collCounter, checkCounter, "left", 0, sackG)

            # check-right
            checkLeftorRight(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action,
                             coord, collCounter, checkCounter, "right", 0, sackG)

    # wenn in der Distanz nicht möglich -> CC um mögliche Sprünge / left / right zu checken
    else:
        checkchoices(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord, 0,
                     collCounter, checkCounter, sackG)


def checkchoices(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord, distance,
                 collCounter, checkCounter, sackG):
    global logActionValue
    global queueDepth
    global q

    # Wenn weniger als eine Sekunde bis zur Deadline verbleibt, bearbeite die Queue nicht weiter
    if time.time() + 1 > deadline:
        with q.mutex:   # oder q = Queue()
            q.queue.clear()
        if myc > 4:  # still to be tested
            return

    if not len(ebene) > depth:
        ebene.append([0, 0, 0, 0, 0])
        myc = depth

    # check-sd/cn/su
    checkFront(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord, 0,
               collCounter, checkCounter, sackG)

    # check-left
    checkLeftorRight(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                     collCounter, checkCounter, "left", 0, sackG)

    # check-right
    checkLeftorRight(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                     collCounter, checkCounter, "right", 0, sackG)




asyncio.get_event_loop().run_until_complete(play(show=True))
