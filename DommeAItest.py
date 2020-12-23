#!/usr/bin/env python3

import asyncio
import random
import threading
import time
from datetime import datetime
import json
from queue import Queue
from matplotlib import pyplot, colors

import websockets
from copy import deepcopy

global ebene
global notbremse
global q
global myc
global lock_objekt


def getnewdirection(direction, change):  # bestimme neue Richtung nach Wechsel
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


def getnewpos(x, y, s, direction):  # bestimme neue Position
    if direction == "up":
        return y - s, x
    elif direction == "down":
        return y + s, x
    elif direction == "left":
        return y, x - s
    else:
        return y, x + s


def gegnerboard(state, counter):
    boardenemies = deepcopy(state["cells"])

    if counter % 6 == 0:
        lucke = True
    else:
        lucke = False

    # Noch nicht alles perfekt. Prüft nicht ob er in sich selbst rein crashen würde.
    # Würde es aus performancegründen auch nicht reinbringen (so bleibt unsere Schlange sehr defensiv)

    # Gehe durch alle Spieler die noch aktiv sind
    for p in range(1, int(len(state["players"]) + 1)):
        if state["players"][str(p)]["active"]:
            if not state["you"] == p:

                #   Prüfe erst ob bei Verlangsamung überleben würde, trage ein, dann CN prüfen und eintragen,
                #   als letztes Beschleinigung prüfen und eintragen (Beachte nicht Sonderfall der 6.ten Runde)
                pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                         state["players"][str(p)]["speed"] - 1, state["players"][str(p)]["direction"])
                # Prüfe ob er das Spielfeld verlassen würde, wenn verlangsamt
                if state["height"] - 1 >= pnewy >= 0 and state["width"] - 1 >= pnewx >= 0:
                    boardenemies[pnewy][pnewx] = 7
                    for i in range(1, state["players"][str(p)]["speed"] - 1):
                        if lucke:
                            pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                     1, state["players"][str(p)]["direction"])
                            boardenemies[pnewy][pnewx] = 7
                            break
                        pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                 i, state["players"][str(p)]["direction"])
                        boardenemies[pnewy][pnewx] = 7
                    pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                             state["players"][str(p)]["speed"], state["players"][str(p)]["direction"])
                    # Prüfe ob er das Spielfeld verlassen würde, wenn nichts macht
                    if state["height"] - 1 >= pnewy >= 0 and state["width"] - 1 >= pnewx >= 0:
                        boardenemies[pnewy][pnewx] = 7
                        pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                 state["players"][str(p)]["speed"] + 1,
                                                 state["players"][str(p)]["direction"])
                        # Prüfe ob er das Spielfeld verlassen würde, wenn beschleunigt
                        if state["height"] - 1 >= pnewy >= 0 and state["width"] - 1 >= pnewx >= 0:
                            boardenemies[pnewy][pnewx] = 7

                # Prüfe ob bei links/rechts außerhalb des Spielfeldes, sonst trage ein
                for newd in ["left", "right"]:
                    newdirection = getnewdirection(state["players"][str(p)]["direction"], newd)
                    pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                             state["players"][str(p)]["speed"], newdirection)
                    # Prüfe ob er das Spielfeld verlassen würde, wenn links/rechts
                    if state["height"] - 1 >= pnewy >= 0 and state["width"] - 1 >= pnewx >= 0:
                        boardenemies[pnewy][pnewx] = 7
                        for i in range(1, state["players"][str(p)]["speed"]):
                            if lucke:
                                pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                         1, newdirection)
                                boardenemies[pnewy][pnewx] = 7
                                break
                            pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                     i, newdirection)
                            boardenemies[pnewy][pnewx] = 7
    return boardenemies


def anzeige(state, counter, action, choices, depth):
    # Informationen über den aktuellen Stand des eigenen Spielers
    youx = str(state["players"][str(state["you"])]["x"])
    youy = str(state["players"][str(state["you"])]["y"])
    youdir = str(state["players"][str(state["you"])]["direction"])
    youspeed = str(state["players"][str(state["you"])]["speed"])

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
        pyplot.xlabel("x: " + youx + " y: " + youy + " | direction: " + youdir + " | speed: " + youspeed +
                      "\n" + str(choices) +
                      "\n" + "nächster Zug: " + str(action) + "  |  Tiefe: " + str(depth) + " | Jump in T - " + str(
            5 - ((counter - 2) % 6)))
        pyplot.show(block=False)


def checkchoices(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action):
    global ebene
    global q
    global notbremse
    global myc
    global lock_objekt

    # lock_objekt.acquire()
    myc = depth

    if not len(ebene) > depth:
        ebene.append([0, 0, 0, 0, 0])

    #   Bei Jahreswechsel kann es zu Fehlern (zu kurzen Berechnungen) kommen..
    #   Auch so kann es sein, dass die ersten Berechnungen noch durchkommen, der Rest aber nicht mehr


    # Wenn weniger als eine Sekunde bis zur Deadline verbleibt, bearbeite die Queue nicht weiter
    if time.time() + 1 > deadline:
        notbremse = True
        return

    # werden verwendet, um Ressourcen bei zu schonen, da nurnoch Kopf geprüft werden muss, wenn voriges geprüft wurde
    clearsd = False
    clearcn = False

    # check-slowdown
    newboard = deepcopy(board)
    if speed > 1:
        newy, newx = getnewpos(x, y, speed - 1, direction)
        if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                newboard[newy][newx] = 7
                hit = False
                for i in range(1, speed - 1):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newyy, newxx = getnewpos(x, y, 1, direction)
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        newboard[newyy][newxx] = 7
                        break
                    newyy, newxx = getnewpos(x, y, i, direction)
                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                if not hit:
                    clearsd = True
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, direction, newboard, speed - 1, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, action]))

    # check-nothing
    # if not clearsd:
    newboard = deepcopy(board)
    newy, newx = getnewpos(x, y, speed, direction)
    if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
        if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
            newboard[newy][newx] = 7
            hit = False
            for i in range(1, speed):
                if clearsd:
                    break
                if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                    newyy, newxx = getnewpos(x, y, 1, direction)
                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                    break
                newyy, newxx = getnewpos(x, y, i, direction)
                if not board[newyy][newxx] == 0:
                    hit = True
                    break
                newboard[newyy][newxx] = 7
            if not hit:
                clearcn = True
                ebene[depth][action] += wert
                q.put((checkchoices, [newx, newy, direction, newboard, speed, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, action]))

    # check-speedup
    # if not clearcn:
    newboard = deepcopy(board)
    if speed < 10:
        newy, newx = getnewpos(x, y, speed + 1, direction)
        if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                hit = False
                newboard[newy][newx] = 7
                for i in range(1, speed + 1):
                    if clearcn:
                        break
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newyy, newxx = getnewpos(x, y, 1, direction)
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        newboard[newyy][newxx] = 7
                        break
                    newyy, newxx = getnewpos(x, y, i, direction)

                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                if not hit:
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, direction, newboard, speed + 1, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, action]))

    # check-left and check-right
    for newd in ["left", "right"]:
        newboard = deepcopy(board)
        newdirection = getnewdirection(direction, newd)
        newy, newx = getnewpos(x, y, speed, newdirection)
        if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                newboard[newy][newx] = 7
                hit = False
                for i in range(1, speed):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newyy, newxx = getnewpos(x, y, 1, newdirection)
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        newboard[newyy][newxx] = 7
                        break
                    newyy, newxx = getnewpos(x, y, i, newdirection)

                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                if not hit:
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, newdirection, newboard, speed, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, action]))
    # lock_objekt.release()


def play():
    global ebene
    global q
    global myc
    global notbremse
    global lock_objekt
    # filename = 'apikey.txt'
    #
    # url = "wss://msoll.de/spe_ed"
    # key = open(filename, "r").read().strip()
    #
    # async with websockets.connect(f"{url}?key={key}") as websocket:
    #     print("Waiting for initial state...", flush=True)
    counter = 0
    choices_actions = ["speed_up", "slow_down", "change_nothing", "turn_left", "turn_right"]
    wert = 1
    show = True  # Bestimmt, ob das GUI angezeigt wird

    # state_json = await websocket.recv()
    state = {'width': 68, 'height': 47, 'cells': [
        [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4,
            4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
            4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 0, 0, 0, 0, 0, 0, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 0, 0, 0, 0, 0, 0, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
            3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 0, 0, 0, 0, 0, 0, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 3, 3, 0, 0, 0, 3, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 4, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 3, 3, 0, 0, 0, 3, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 4, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 3, 3, 0, 0, 0, 3, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 3, 3, 0, 0, 0, 3, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 3, 3, 0, 0, 0, 3, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 4, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
            3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
            4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4,
            4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
            4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 4, 4, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 4, 4, 0, 4, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 4, 4, 0, 4, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 4, 0, 4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], [
            4, 0, 0, 0, 0, 0, 0, 1, 0, 4, 4, 0, 4, 0, 4, 4, 4, 4, 4, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], [
            4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 4, 0, 4, 0, 0, 0, 0, 4, 4, 4, 0, 4, 0, 4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], [
            4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 4, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 4, 0, 4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], [
            0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], [
            0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 4,
            4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0]],
             'players': {
                 '1': {'x': 7, 'y': 47, 'direction': 'down', 'speed': 5, 'active': False},
                 '2': {'x': 25, 'y': -1, 'direction': 'up', 'speed': 1, 'active': False},
                 '3': {'x': 51, 'y': 22, 'direction': 'up', 'speed': 1, 'active': True},
                 '4': {'x': 26, 'y': 45, 'direction': 'up', 'speed': 1, 'active': True}},
             'you': 4, 'running': True, 'deadline': '2020-12-22T15:06:40Z'}
    # print("<", state)
    # print("Startzeit: " + str(datetime.utcnow()))
    own_player = state["players"][str(state["you"])]
    # if not state["running"] or not own_player["active"]:
    #     if not own_player["active"]:
    #         erfolg = "verloren"
    #     else:
    #         valid_responses = ["Winner Winner, Chicken Dinner", "git gud", "Too weak, too slow",
    #                            "ez game, ez life", "ez pz lemon squeezy", "ez", "rekt", "l2p", "noobs",
    #                            "too ez"]
    #         erfolg = random.choice(valid_responses)
    #     print(erfolg)
    #     pyplot.show()
    #     break

    # Initialisierung
    depth = 0
    counter += 1
    choices = [0, 0, 0, 0, 0]
    ebene = [[0, 0, 0, 0, 0]]
    q = Queue()
    clearsd = False
    clearcn = False
    notbremse = False
    lock_objekt = threading.Lock()
    deadline = time.time()+15

    # Erstelle ein Board mit allen möglichen Zügen der aktiven Gegner, um Überschneidungen im nächsten Schritt
    # zu verhindern. Berücksichtigt nur Züge, bei denen der Gegner nicht außerhalb des Feldes landet
    boardenemies = gegnerboard(state, counter)
    # lock_objekt.acquire()
    # check-slowdown
    board = deepcopy(boardenemies)
    if own_player["speed"] > 1:
        newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"] - 1, own_player["direction"])
        # Prüfe ob er das Spielfeld verlassen würde
        if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
            if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                board[newy][newx] = 7
                hit = False
                for i in range(1, own_player["speed"] - 1):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newyy, newxx = getnewpos(own_player["x"], own_player["y"], 1, own_player["direction"])
                        if not state["cells"][newyy][newxx] == 0:
                            hit = True
                            break
                        board[newyy][newxx] = 7
                        break
                    newyy, newxx = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                    if not state["cells"][newyy][newxx] == 0:
                        hit = True
                        break
                    board[newyy][newxx] = 7
                if not hit:
                    clearsd = True
                    ebene[depth][1] += wert
                    q.put((checkchoices, [newx, newy, own_player["direction"], board,
                                          own_player["speed"] - 1, state["width"],
                                          state["height"], wert / 2, depth + 1, counter + 1, deadline, 1]))

    # check-nothing
    # if not clearsd:
    board = deepcopy(boardenemies)
    newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"], own_player["direction"])
    # Prüfe ob er das Spielfeld verlassen würde
    if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
        if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
            board[newy][newx] = 7
            hit = False
            for i in range(1, own_player["speed"]):
                if clearsd:
                    break
                if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                    newyy, newxx = getnewpos(own_player["x"], own_player["y"], 1, own_player["direction"])
                    if not state["cells"][newyy][newxx] == 0:
                        hit = True
                        break
                    board[newyy][newxx] = 7
                    break
                newyy, newxx = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                if not state["cells"][newyy][newxx] == 0:
                    hit = True
                    break
                board[newyy][newxx] = 7
            if not hit:
                clearcn = True
                ebene[depth][2] += wert
                q.put((checkchoices, [newx, newy, own_player["direction"], board,
                                      own_player["speed"], state["width"], state["height"], wert / 2,
                                      depth + 1, counter + 1, deadline, 2]))

    # check-speedup
    # if not clearcn:
    board = deepcopy(boardenemies)
    if own_player["speed"] < 10:
        newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"] + 1, own_player["direction"])
        # Prüfe ob er das Spielfeld verlassen würde
        if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
            if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                board[newy][newx] = 7
                hit = False
                for i in range(1, own_player["speed"] + 1):
                    if clearcn:
                        break
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newyy, newxx = getnewpos(own_player["x"], own_player["y"], 1, own_player["direction"])
                        if not state["cells"][newyy][newxx] == 0:
                            hit = True
                            break
                        board[newyy][newxx] = 7
                        break
                    newyy, newxx = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                    if not state["cells"][newyy][newxx] == 0:
                        hit = True
                        break
                    board[newyy][newxx] = 7

                if not hit:
                    ebene[depth][0] += wert
                    q.put((checkchoices, [newx, newy, own_player["direction"],
                                          board, own_player["speed"] + 1, state["width"],
                                          state["height"], wert / 2, depth + 1, counter + 1, deadline, 0]))

    # check-left
    board = deepcopy(boardenemies)
    newdirection = getnewdirection(own_player["direction"], "left")
    newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"], newdirection)
    # Prüfe ob er das Spielfeld verlassen würde
    if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
        if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
            board[newy][newx] = 7
            hit = False
            for i in range(1, own_player["speed"]):
                if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                    newyy, newxx = getnewpos(own_player["x"], own_player["y"], 1, newdirection)
                    if not state["cells"][newyy][newxx] == 0:
                        hit = True
                        break
                    board[newyy][newxx] = 7
                    break
                newyy, newxx = getnewpos(own_player["x"], own_player["y"], i, newdirection)
                if not state["cells"][newyy][newxx] == 0:
                    hit = True
                    break
                board[newyy][newxx] = 7
            if not hit:
                ebene[depth][3] += wert
                q.put((checkchoices, [newx, newy, newdirection, board,
                                      own_player["speed"], state["width"], state["height"],
                                      wert / 2, depth + 1, counter + 1, deadline, 3]))

    # check-right
    board = deepcopy(boardenemies)
    newdirection = getnewdirection(own_player["direction"], "right")
    newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"], newdirection)
    # Prüfe ob er das Spielfeld verlassen würde
    if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
        if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
            board[newy][newx] = 7
            hit = False
            for i in range(1, own_player["speed"]):
                if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                    newyy, newxx = getnewpos(own_player["x"], own_player["y"], 1, newdirection)
                    if not state["cells"][newyy][newxx] == 0:
                        hit = True
                        break
                    board[newyy][newxx] = 7
                    break
                newyy, newxx = getnewpos(own_player["x"], own_player["y"], i, newdirection)
                if not state["cells"][newyy][newxx] == 0:
                    hit = True
                    break
                board[newyy][newxx] = 7
            if not hit:
                ebene[depth][4] += wert
                q.put((checkchoices, [newx, newy, newdirection, board,
                                      own_player["speed"], state["width"], state["height"],
                                      wert / 2, depth + 1, counter + 1, deadline, 4]))
    # lock_objekt.release()
    # Bearbeite solange Objekte aus der Queue bis diese leer ist oder 1 Sekunde bis zur Deadline verbleibt
    while not q.empty() and not notbremse:
        f, args = q.get()
        f(*args)

    # Züge, die tiefere Ebenen erreichen, werden deutlich bevorzugt (+100)
    print(ebene)
    for i in range(0, 5):
        if myc > 0:
            if ebene[myc - 1][i] != 0:
                ebene[0][i] += 100

    for i in range(0, myc):
        for j in range(0, 5):
            choices[j] += ebene[i][j]

    # Sonderfall myc=0 (sehr unwahrscheinlich). Vollständigkeitshalber dabei
    if myc == 0:
        choices = ebene[0]

    # Wähle von den möglichen Zügen den bestbewertesten aus und gebe diesen aus.
    # Falls 2 Züge gleich gut sind, dann wähle zufällig einen der beiden aus
    print(choices)
    best = max(choices)
    action = choices_actions[choices.index(best)]
    randy = []
    for i in range(len(choices)):
        if choices[i] == best:
            randy.append(choices_actions[i])
    if len(randy) > 1:
        action = random.choice(randy)
    print("Endzeit: " + str(datetime.utcnow()))
    print(">", action)
    if show:  # GUI, falls show == True
        anzeige(state, counter, action, choices, myc - 1)
#         await websocket.send(action_json)
#
#
play()
