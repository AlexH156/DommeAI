#!/usr/bin/env python3

import asyncio
import random
import time
from datetime import datetime
import json
from queue import Queue
from matplotlib import pyplot, colors
import dateutil.parser as dp
import websockets

# TODO alles optimieren->höhere Tiefe möglich
# TODO alles aufhübschen (keine Prio)
# TODO evtl: teilweise berechnete Ebenen mit Durchschnitt berechnen lassen (keine Prio)
# TODO Evtl. im Endgame langsame Geschwindigkeit bevorzugen
# TODO sd,cn,su vll schöner umschreiben
# TODO Checkcounter prüfen
# TODO Globalität prüfen (Notwendigkeit allgemein und erneute Aufzählungen)

# TODO Deadline in GUI (verfügbare Zeit)
# TODO evtl Time API einbauen

global ebene
global notbremse
global q
global myc

global checkD  # Debugging


def calcAction(choices_actions):
    choices = [0, 0, 0, 0, 0]
    randy = []

    # Züge, die tiefere Ebenen erreichen, werden deutlich bevorzugt (+100)
    print(ebene)
    for i in range(0, 5):
        if myc > 0:
            if ebene[myc - 1][i] != 0:
                ebene[0][i] += 10000
        else:
            choices = ebene[0]

    for i in range(0, myc):
        for j in range(0, 5):
            choices[j] += ebene[i][j]

    # Wähle von den möglichen Zügen den bestbewertesten aus und gebe diesen aus.
    # Falls 2 Züge gleich gut sind, dann wähle zufällig einen der beiden aus
    print(choices)
    best = max(choices)
    action = choices_actions[choices.index(best)]

    for i in range(len(choices)):
        if choices[i] == best:
            randy.append(choices_actions[i])
    if len(randy) > 1:
        action = random.choice(randy)

    return action, choices


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
    newaction = action
    init = action is None
    isCCStraight = checkCounter < 3  # True, wenn Koordinaten nicht geprüft werden müssen
    isJump = counter % 6 == 0
    newcoord = coord[:]

    # Vorgehen: Bei Sprung prüfe erst gemeinsamen Schwanz, dann jeweils Kopf
    # Vorgehen: Bei nicht-Sprung prüfe sd komplett, dann Kopf cn, dann Kopf su
    if isJump:
        newbodyY, newbodyX = getnewpos(x, y, 1, direction)
        if height > newbodyY >= 0 and width > newbodyX >= 0 and board[newbodyY][newbodyX] == 0 and (
                isCCStraight or [newbodyY, newbodyX] not in coord):
            newcoord.append([newbodyY, newbodyX])
            newheadY, newheadX = getnewpos(x, y, speed - 1, direction)
            if speed > 1 and height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    isCCStraight or [newheadY, newheadX] not in coord):
                newcoord0 = newcoord[:]
                if speed > 2:
                    newcoord0.append([newheadY, newheadX])
                if init:
                    newaction = 1
                ebene[depth][newaction] += wert
                if sackG and overSnake(x, y, board, direction, speed-1) and not deadend(newheadX, newheadY, board, direction, width, height) < 14:
                    ebene[depth][newaction] += 500
                q.put((checkchoices, [newheadX, newheadY, direction, board, speed - 1, width, height, wert / 2,
                                   depth + 1, counter + 1, deadline, newaction, newcoord0, distance, 0, checkCounter,
                                   sackG]))
            newheadY, newheadX = getnewpos(x, y, speed, direction)
            if height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    isCCStraight or [newheadY, newheadX] not in coord):
                newcoord1 = newcoord[:]
                if speed > 1:
                    newcoord1.append([newheadY, newheadX])
                if init:
                    newaction = 2
                ebene[depth][newaction] += wert
                if sackG and overSnake(x, y, board, direction, speed) and not deadend(newheadX, newheadY, board, direction, width, height) < 14:
                    ebene[depth][newaction] += 500
                q.put((checkchoices, [newheadX, newheadY, direction, board, speed, width, height, wert / 2,
                                   depth + 1, counter + 1, deadline, newaction, newcoord1, distance, 0, checkCounter,
                                   sackG]))
            newheadY, newheadX = getnewpos(x, y, speed + 1, direction)

            if speed < 10 and height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    isCCStraight or [newheadY, newheadX] not in coord):
                newcoord2 = newcoord[:]
                newcoord2.append([newheadY, newheadX])
                if init:
                    newaction = 0
                ebene[depth][newaction] += wert
                if sackG and overSnake(x, y, board, direction, speed+1) and not deadend(newheadX, newheadY, board, direction, width, height) < 14:
                    ebene[depth][newaction] += 500
                q.put((checkchoices, [newheadX, newheadY, direction, board, speed + 1, width, height, wert / 2,
                                   depth + 1, counter + 1, deadline, newaction, newcoord2, distance, 0, checkCounter,
                                   sackG]))
    else:
        newcoord0 = coord[:]
        hit = False
        if speed > 1:
            newheadY, newheadX = getnewpos(x, y, speed - 1, direction)
            if height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    isCCStraight or [newheadY, newheadX] not in coord):
                newcoord0.append([newheadY, newheadX])
                for i in range(1, speed - 1):
                    newbodyY, newbodyX = getnewpos(x, y, i, direction)
                    if board[newbodyY][newbodyX] != 0 or (not isCCStraight and [newbodyY, newbodyX] in coord):
                        hit = True
                        break
                    newcoord0.append([newbodyY, newbodyX])
                if not hit:
                    if init:
                        newaction = 1
                    ebene[depth][newaction] += wert
                    q.put((checkchoices, [newheadX, newheadY, direction, board, speed - 1, width, height, wert / 2,
                                       depth + 1, counter + 1, deadline, newaction, newcoord0, distance, 0,
                                       checkCounter, sackG]))
            else:
                hit = True
        if not hit:
            newheadY, newheadX = getnewpos(x, y, speed, direction)
            if height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (
                    isCCStraight or [newheadY, newheadX] not in coord):
                newcoord1 = newcoord0[:]
                newcoord1.append([newheadY, newheadX])
                if init:
                    newaction = 2
                ebene[depth][newaction] += wert
                q.put((checkchoices, [newheadX, newheadY, direction, board, speed, width, height, wert / 2,
                                   depth + 1, counter + 1, deadline, newaction, newcoord1, distance, 0, checkCounter,
                                   sackG]))
                newheadY, newheadX = getnewpos(x, y, speed + 1, direction)
                if speed < 10 and height > newheadY >= 0 and width > newheadX >= 0 and board[newheadY][
                    newheadX] == 0 and (isCCStraight or [newheadY,newheadX] not in coord):
                    newcoord2 = newcoord1[:]
                    newcoord2.append([newheadY, newheadX])
                    if init:
                        newaction = 0
                    ebene[depth][newaction] += wert
                    q.put((checkchoices, [newheadX, newheadY, direction, board, speed + 1, width, height, wert / 2,
                                       depth + 1, counter + 1, deadline, newaction, newcoord2, distance, 0,
                                       checkCounter, sackG]))


def checkLeftorRight(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                     collCounter, checkCounter, change, distance, sackG):
    coordIgnore = checkCounter < 2
    direction = getnewdirection(direction, change)
    isJump = counter % 6 == 0
    newcoord = coord[:]

    newheadY, newheadX = getnewpos(x, y, speed, direction)
    if (change == "left" and collCounter != -2 or change == "right" and collCounter != 2) and height > newheadY >= 0 \
            and width > newheadX >= 0 and board[newheadY][newheadX] == 0 and (coordIgnore or [newheadY, newheadX] not in coord):
        isHit = False
        newcoord.append([newheadY, newheadX])
        for i in range(1, speed):
            if isJump:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
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
            ebene[depth][action] += wert
            if isJump and sackG and overSnake(x, y, board, direction, speed) and not deadend(newheadX, newheadY, board, direction, width, height) < 14:
                ebene[depth][action] += 500
            if change == "left":
                if collCounter > 0:
                    checkCounter -= 1
                else:
                    checkCounter += 1
                collCounter = min(collCounter - 1, - 1)
            else:
                if collCounter < 0:
                    checkCounter -= 1
                else:
                    checkCounter += 1
                collCounter = max(collCounter + 1, 1)
            q.put((checkdistance, [newheadX, newheadY, direction, board, speed, width, height, wert / 2, depth + 1,
                                       counter + 1, deadline, action, newcoord, distance - speed, collCounter,
                                       checkCounter, sackG]))


# Diese Methode trägt alle legalen Züge der Gegner ein, um Überschneidungen zu vermeiden.
def gegnerboard(state, isJump):
    board = [row[:] for row in state["cells"]]
    # Gehe durch alle Spieler die noch aktiv sind
    for p in range(1, int(len(state["players"]) + 1)):
        if state["players"][str(p)]["active"] and not state["you"] == p:
            # Prüfe erst ob bei Verlangsamung überleben würde, trage ein, dann CN prüfen und eintragen,
            # als letztes Beschleinigung prüfen und eintragen (Beachte nicht Sonderfall der 6.ten Runde)
            pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                     state["players"][str(p)]["speed"] - 1, state["players"][str(p)]["direction"])
            # Prüfe ob er das Spielfeld verlassen würde, wenn verlangsamt
            if state["height"] > pnewy >= 0 and state["width"] > pnewx >= 0:
                board[pnewy][pnewx] = 7
                for i in range(1, state["players"][str(p)]["speed"] - 1):
                    if isJump:
                        pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                 1, state["players"][str(p)]["direction"])
                        board[pnewy][pnewx] = 7
                        break
                    pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                             i, state["players"][str(p)]["direction"])
                    board[pnewy][pnewx] = 7
                pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                         state["players"][str(p)]["speed"], state["players"][str(p)]["direction"])
                # Prüfe ob er das Spielfeld verlassen würde, wenn nichts macht
                if state["height"] > pnewy >= 0 and state["width"] > pnewx >= 0:
                    board[pnewy][pnewx] = 7
                    pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                             state["players"][str(p)]["speed"] + 1,
                                             state["players"][str(p)]["direction"])
                    # Prüfe ob er das Spielfeld verlassen würde, wenn beschleunigt
                    if state["height"] > pnewy >= 0 and state["width"] > pnewx >= 0:
                        board[pnewy][pnewx] = 7

            # Prüfe ob bei links/rechts außerhalb des Spielfeldes, sonst trage ein
            for newd in ["left", "right"]:
                newdirection = getnewdirection(state["players"][str(p)]["direction"], newd)
                pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                         state["players"][str(p)]["speed"], newdirection)
                # Prüfe ob er das Spielfeld verlassen würde, wenn links/rechts
                if state["height"] > pnewy >= 0 and state["width"] > pnewx >= 0:
                    board[pnewy][pnewx] = 7
                    for i in range(1, state["players"][str(p)]["speed"]):
                        if isJump:
                            pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                     1, newdirection)
                            board[pnewy][pnewx] = 7
                            break
                        pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                 i, newdirection)
                        board[pnewy][pnewx] = 7
    return board


def distanz(px, py, board, direction, width, height):
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


def overSnake(x, y, board, direction, speed):
    if speed < 3:
        return False
    for i in range(2,speed):
        newy, newx = getnewpos(x, y, i, direction)
        if board[newy][newx] != 0:
            print("Über Schlange" + str(newy) + " " + str(newx))
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
    global ebene
    global q
    global notbremse
    global myc

    global checkD
    checkD += 1  # Debugging

    if not len(ebene) > depth:
        ebene.append([0, 0, 0, 0, 0])
        myc = depth

    # Wenn weniger als eine Sekunde bis zur Deadline verbleibt, bearbeite die Queue nicht weiter
    if time.time() + 1 > deadline:
        if myc > 4:  # still to be tested
            notbremse = True
            return

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
        isJump = counter % 6 == 0

        newcoord = coord[:]

        # ist es evtl im nächsten Schritt möglich? -> CD
        if isJump:
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
    # collCounter: +1 wenn rechts, -1 wenn links, =0 wenn vorne
    # collCounter == 2: checkright muss nicht geprüft werden
    # collCounter == -2: checkleft muss nicht geprüft werden
    # checkCounter: +1 wenn rechts, -1 wenn links, +0 wenn vorne
    # 3 > checkCounter > -3 : Koordinaten müssen nach vorne nicht geprüft werden
    # checkCounter < 2: bei checkright müssen coords nicht geprüft werden
    # checkCounter > -2: bei checkleft müssen coords nicht geprüft werden

    global ebene
    global notbremse
    global myc

    if not len(ebene) > depth:
        ebene.append([0, 0, 0, 0, 0])
        myc = depth

        # Wenn weniger als eine Sekunde bis zur Deadline verbleibt, bearbeite die Queue nicht weiter
    if time.time() + 1 > deadline:
        if myc > 4:  # still to be tested
            notbremse = True
            return

    # check-sd/cn/su
    checkFront(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord, 0,
               collCounter, checkCounter, sackG)

    # check-left
    checkLeftorRight(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                     collCounter, checkCounter, "left", 0, sackG)

    # check-right
    checkLeftorRight(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                     collCounter, checkCounter, "right", 0, sackG)


async def play():
    global ebene
    global q
    global myc
    global notbremse

    global checkD  # Debugging

    filename = 'apikey.txt'
    url = "wss://msoll.de/spe_ed"
    key = open(filename, "r").read().strip()
    async with websockets.connect(f"{url}?key={key}") as websocket:
        print("Waiting for initial state...", flush=True)
        counter = 0
        choices_actions = ["speed_up", "slow_down", "change_nothing", "turn_left", "turn_right"]
        show = True  # Bestimmt, ob das GUI angezeigt wird

        while True:
            state_json = await websocket.recv()
            state = json.loads(state_json)
            print("<", state)
            print("Startzeit: " + str(datetime.utcnow()))
            own = state["players"][str(state["you"])]
            if not state["running"] or not own["active"]:
                if not own["active"]:
                    erfolg = "verloren"
                else:
                    valid_responses = ["Winner Winner, Chicken Dinner", "git gud", "Too weak, too slow",
                                       "ez game, ez life", "ez pz lemon squeezy", "ez", "rekt", "l2p", "noobs",
                                       "too ez"]
                    erfolg = random.choice(valid_responses)
                print(erfolg)
                pyplot.show()
                break

            # Initialisierung
            myc, depth = 0, 0
            counter += 1
            isJump = counter % 6 == 0
            ebene = [[0, 0, 0, 0, 0]]
            q = Queue()
            notbremse = False
            deadline = dp.parse(state["deadline"]).timestamp()
            checks, checkD = 0, 0  # Debugging

            # Erstelle ein Board mit allen möglichen Zügen der aktiven Gegner, um Überschneidungen im nächsten Schritt
            # zu verhindern. Berücksichtigt alle Züge, bei denen der Gegner nicht außerhalb des Feldes landet
            board = gegnerboard(state, isJump)
            # board = [row[:] for row in state["cells"]]

            LR = maxLR(own["x"], own["y"], board, own["direction"], state["width"], state["height"])
            deDir = deadendDir(own["x"], own["y"], board, own["direction"], state["width"], state["height"])
            de = deadend(own["x"], own["y"], board, own["direction"], state["width"], state["height"])
            sackG = False
            if de < 14:
                sackG = True

            # print("distanz nach vorne:", vorne)
            # print("rechts:", rechts)
            # print("links:", links)

            # check sd,cn, su
            for ka in [board, state["cells"]]:
                # Prüfe Abstand nach Vorne, Links und Rechts
                vorne = distanz(own["x"], own["y"], ka, own["direction"], state["width"], state["height"])
                links = distanz(own["x"], own["y"], ka, getnewdirection(own["direction"], "left"), state["width"], state["height"])
                rechts = distanz(own["x"], own["y"], ka, getnewdirection(own["direction"], "right"), state["width"], state["height"])
                if vorne > own["speed"]:
                    checkWhat = checkdistance
                else:
                    checkWhat = checkFront

                checkWhat(own["x"], own["y"], own["direction"], ka, own["speed"],
                          state["width"], state["height"], 1, depth, counter, deadline, None, [], vorne, 0, 0, sackG)

                # check-left
                checkLeftorRight(own["x"], own["y"], own["direction"], ka, own["speed"],
                                 state["width"],
                                 state["height"], 1, depth, counter, deadline, 3, [], 0, 0, "left", links, sackG)

                # check-right
                checkLeftorRight(own["x"], own["y"], own["direction"], ka, own["speed"],
                                 state["width"],
                                 state["height"], 1, depth, counter, deadline, 4, [], 0, 0, "right", rechts, sackG)

                # Bearbeite solange Objekte aus der Queue bis diese leer ist oder 1 Sekunde bis zur Deadline verbleibt
                while not q.empty() and not notbremse:
                    checks += 1  # Debugging
                    f, args = q.get()
                    f(*args)

                if myc > 0:
                    break

            action, choices = calcAction(choices_actions)

            print("Endzeit: " + str(datetime.utcnow()))
            print(">", action)

            print("\n", checks, "davon checkD:", checkD)

            action_json = json.dumps({"action": action})
            if show:  # GUI, falls show == True
                anzeige(state, counter, action, choices, myc - 1, LR, de, deDir, sackG)
            await websocket.send(action_json)


asyncio.get_event_loop().run_until_complete(play())
