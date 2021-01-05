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
from copy import deepcopy

# TODO alles optimieren->höhere Tiefe möglich
# TODO alles aufhübschen (keine Prio)
# TODO evtl: teilweise berechnete Ebenen mit Durchschnitt berechnen lassen (keine Prio)
# TODO Evtl. im Endgame langsame Geschwindigkeit bevorzugen
# TODO Berechnung abbrechen, wenn nur noch eine Möglichkeit auf der Ebene (Optimierung für Machine Learning etc)
# TODO / Problem: Domme merkt zu spät, wenn er in eine Sackgasse geht - evtl Sprünge größer gewichten?
# TODO evtl: Counter an berechneten Möglichkeiten zum Debuggen der Effizienz einbauen
# TODO Platz nach vorne/links/rechts checken und optimieren
# TODO Sprünge bevorzugen, wenn das Maximum des Platzes nach vorne kleiner als x
# TODO Wenn alle choices 0 dann nochmal prüfen und nicht zufall (bei len(randy) > 1)
# TODO In CheckChoices die Prüfungen zusammen fassen (Optik)

global ebene
global notbremse
global q
global myc


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


# Diese Methode trägt alle legalen Züge der Gegner ein, um Überschneidungen zu vermeiden.
def gegnerboard(state, sprung):
    boardenemies = deepcopy(state["cells"])
    # TODO: prüfen, ob deepcopy nötig. Evtl einfach state["cells"] benutzen (überschreibt das das ursprüngliche?)
    # Gehe durch alle Spieler die noch aktiv sind
    for p in range(1, int(len(state["players"]) + 1)):
        if state["players"][str(p)]["active"] and not state["you"] == p:
            # Prüfe erst ob bei Verlangsamung überleben würde, trage ein, dann CN prüfen und eintragen,
            # als letztes Beschleinigung prüfen und eintragen (Beachte nicht Sonderfall der 6.ten Runde)
            pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                     state["players"][str(p)]["speed"] - 1, state["players"][str(p)]["direction"])
            # Prüfe ob er das Spielfeld verlassen würde, wenn verlangsamt
            if state["height"] > pnewy >= 0 and state["width"] > pnewx >= 0:
                boardenemies[pnewy][pnewx] = 7
                for i in range(1, state["players"][str(p)]["speed"] - 1):
                    if sprung:
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
                if state["height"] > pnewy >= 0 and state["width"] > pnewx >= 0:
                    boardenemies[pnewy][pnewx] = 7
                    pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                             state["players"][str(p)]["speed"] + 1,
                                             state["players"][str(p)]["direction"])
                    # Prüfe ob er das Spielfeld verlassen würde, wenn beschleunigt
                    if state["height"] > pnewy >= 0 and state["width"] > pnewx >= 0:
                        boardenemies[pnewy][pnewx] = 7

            # Prüfe ob bei links/rechts außerhalb des Spielfeldes, sonst trage ein
            for newd in ["left", "right"]:
                newdirection = getnewdirection(state["players"][str(p)]["direction"], newd)
                pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                         state["players"][str(p)]["speed"], newdirection)
                # Prüfe ob er das Spielfeld verlassen würde, wenn links/rechts
                if state["height"] > pnewy >= 0 and state["width"] > pnewx >= 0:
                    boardenemies[pnewy][pnewx] = 7
                    for i in range(1, state["players"][str(p)]["speed"]):
                        if sprung:
                            pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                     1, newdirection)
                            boardenemies[pnewy][pnewx] = 7
                            break
                        pnewy, pnewx = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                 i, newdirection)
                        boardenemies[pnewy][pnewx] = 7
    return boardenemies


def distanz(state, direction):
    board = state["cells"]
    width = state["width"]
    height = state["height"]
    own_player = state["players"][str(state["you"])]
    px = own_player["x"]
    py = own_player["y"]
    dis = -1
    if direction == "up":
        while py >= 0 and board[py][px] == 0:
            py -= 1
            dis += 1
    elif direction == "down":
        while py < height and board[py][px] == 0:
            py += 1
            dis += 1
    elif direction == "right":
        while px < width and board[py][px] == 0:
            px += 1
            dis += 1
    else:
        while px >= 0 and board[py][px] == 0:
            px -= 1
            dis += 1
    return dis


def anzeige(state, counter, action, choices, depth):
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
        pyplot.xlabel("x: " + youx + " y: " + youy + " | direction: " + youdir + " | speed: " + youspeed +
                      "\n" + str(choices) +
                      "\n" + "nächster Zug: " + str(action) + "  |  Tiefe: " + str(depth) + " | Jump in T - " + str(
            5 - ((counter - 2) % 6)))
        pyplot.show(block=False)


def checkdistance(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                  actionlist, newaction, distance):
    global ebene
    global q
    global notbremse
    global myc

    myc = depth

    #actionlist.append(newaction)

    if not len(ebene) > depth:
        ebene.append([0, 0, 0, 0, 0])

    sprung = False

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
    if distance >= (speed + 1):

        if counter % 6 == 0:
            sprung = True

        newcoord = coord[:]

        # ist es evtl im nächsten Schritt möglich? -> CD
        if distance > (speed + 1):
            if sprung:
                newy, newx = getnewpos(x, y, 1, direction)
                newcoord.append([newy, newx])

                # speed_down in queue
                if speed > 1:
                    newcoord0 = newcoord[:]
                    newcoord0.append([newy, newx])
                    ebene[depth][action] += wert
                    q.put((checkdistance, [newx, newy, direction, board, speed - 1, width, height, wert / 2,
                                           depth + 1, counter + 1, deadline, action, newcoord0, [], 1,
                                           distance - (speed - 1)]))

                # change_nothing
                newy, newx = getnewpos(x, y, speed, direction)
                newcoord1 = newcoord[:]
                newcoord1.append([newy, newx])
                ebene[depth][action] += wert
                q.put((checkdistance, [newx, newy, direction, board, speed, width, height, wert / 2,
                                       depth + 1, counter + 1, deadline, action, newcoord1, [], 2, distance - speed]))
                # speed_up
                if speed < 10:
                    newy, newx = getnewpos(x, y, speed + 1, direction)
                    newcoord2 = newcoord[:]
                    newcoord2.append([newy, newx])
                    ebene[depth][action] += wert
                    q.put((checkdistance, [newx, newy, direction, board, speed + 1, width, height, wert / 2,
                                           depth + 1, counter + 1, deadline, action, newcoord2, [], 0,
                                           distance - (speed + 1)]))
            else:
                if speed > 1:
                    for i in range(1, speed - 1):
                        newyy, newxx = getnewpos(x, y, i, direction)
                        newcoord.append([newyy, newxx])
                    # speed_down
                    ebene[depth][action] += wert
                    newy, newx = getnewpos(x, y, speed - 1, direction)
                    q.put((checkdistance, [newx, newy, direction, board, speed - 1, width, height, wert / 2,
                                           depth + 1, counter + 1, deadline, action, newcoord, [], 1,
                                           distance - (speed - 1)]))
                # change_nothing
                newy, newx = getnewpos(x, y, speed, direction)
                newcoord1 = newcoord[:]
                newcoord1.append([newy, newx])
                ebene[depth][action] += wert
                q.put((checkdistance, [newx, newy, direction, board, speed, width, height, wert / 2,
                                       depth + 1, counter + 1, deadline, action, newcoord1, [], 2, distance - speed]))

                # speed_up
                if speed < 10:
                    newy, newx = getnewpos(x, y, speed + 1, direction)
                    newcoord2 = newcoord[:]
                    newcoord2.append([newy, newx])
                    ebene[depth][action] += wert
                    q.put((checkdistance, [newx, newy, direction, board, speed, width, height, wert / 2,
                                           depth + 1, counter + 1, deadline, action, newcoord2, [], 2,
                                           distance - (speed + 1)]))

        # nur in diesem schritt möglich -> CC
        else:
            if sprung:
                newy, newx = getnewpos(x, y, 1, direction)
                newcoord.append([newy, newx])

                # speed_down in queue
                if speed > 1:
                    newcoord0 = newcoord[:]
                    newcoord0.append([newy, newx])
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, direction, board, speed - 1, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, action, newcoord0, [], 1]))

                # change_nothing
                newy, newx = getnewpos(x, y, speed, direction)
                newcoord1 = newcoord[:]
                newcoord1.append([newy, newx])
                ebene[depth][action] += wert
                q.put((checkchoices, [newx, newy, direction, board, speed, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, action, newcoord1, [], 2]))
                # speed_up
                if speed < 10:
                    newy, newx = getnewpos(x, y, speed + 1, direction)
                    newcoord2 = newcoord[:]
                    newcoord2.append([newy, newx])
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, direction, board, speed + 1, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, action, newcoord2, [], 0]))
            else:
                if speed > 1:
                    for i in range(1, speed - 1):
                        newyy, newxx = getnewpos(x, y, i, direction)
                        newcoord.append([newyy, newxx])
                    # speed_down
                    ebene[depth][action] += wert
                    newy, newx = getnewpos(x, y, speed - 1, direction)
                    q.put((checkchoices, [newx, newy, direction, board, speed - 1, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, action, newcoord, [], 1]))
                # change_nothing
                newy, newx = getnewpos(x, y, speed, direction)
                newcoord1 = newcoord[:]
                newcoord1.append([newy, newx])
                ebene[depth][action] += wert
                q.put((checkchoices, [newx, newy, direction, board, speed, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, action, newcoord1, [], 2]))

                # speed_up
                if speed < 10:
                    newy, newx = getnewpos(x, y, speed + 1, direction)
                    newcoord2 = newcoord[:]
                    newcoord2.append([newy, newx])
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, direction, board, speed, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, action, newcoord2, [], 2]))

        # checkleft, checkright von cc

        # check-left
        newcoord3 = coord[:]
        newdirection = getnewdirection(direction, "left")
        newy, newx = getnewpos(x, y, speed, newdirection)
        if height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0:
            hit = False
            newcoord3.append([newy, newx])
            for i in range(1, speed):
                if sprung:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                    newyy, newxx = getnewpos(x, y, 1, newdirection)
                    if board[newyy][newxx] != 0:
                        hit = True
                        break
                    newcoord3.append([newyy, newxx])
                    break
                newyy, newxx = getnewpos(x, y, i, newdirection)
                if board[newyy][newxx] != 0:
                    hit = True
                    break
                newcoord3.append([newyy, newxx])
            if not hit:
                ebene[depth][action] += wert
                q.put((checkchoices, [newx, newy, newdirection, board, speed, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, action, newcoord3, [], 3]))

        # check-right
        newcoord4 = coord[:]
        newdirection = getnewdirection(direction, "right")
        newy, newx = getnewpos(x, y, speed, newdirection)
        if height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0:
            hit = False
            newcoord4.append([newy, newx])
            for i in range(1, speed):
                if sprung:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                    newyy, newxx = getnewpos(x, y, 1, newdirection)
                    if board[newyy][newxx] != 0:
                        hit = True
                        break
                    newcoord4.append([newyy, newxx])
                    break
                newyy, newxx = getnewpos(x, y, i, newdirection)
                if board[newyy][newxx] != 0:
                    hit = True
                    break
                newcoord4.append([newyy, newxx])
            if not hit:
                ebene[depth][action] += wert
                q.put((checkchoices, [newx, newy, newdirection, board, speed, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, action, newcoord4, [], 4]))

    # wenn in der Distanz nicht möglich -> CC um mögloiche Sprünge / left / right zu checken
    else:
        checkchoices(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                     [], newaction)


def checkchoices(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action, coord,
                 actionlist, newaction):
    global ebene
    global q
    global notbremse
    global myc

    myc = depth  # TODO kann das nicht hinter ebene.append?
    # rightcoll = False
    # leftcoll = False
    # actionlist.append(newaction)
    #
    #  if len(actionlist) > 1:
    #     if actionlist[len(actionlist) - 1] == 3 and actionlist[len(actionlist) - 2] == 3:
    #         leftcoll = True
    #     if actionlist[len(actionlist) - 1] == 4 and actionlist[len(actionlist) - 2] == 4:
    #         rightcoll = True

    if not len(ebene) > depth:
        ebene.append([0, 0, 0, 0, 0])

    # Wenn weniger als eine Sekunde bis zur Deadline verbleibt, bearbeite die Queue nicht weiter
    if time.time() + 1 > deadline:
        notbremse = True
        return

    if counter % 6 == 0:
        sprung = True
    else:
        sprung = False

    # check sd,cn,su
    newcoord = coord[:]
    if sprung:
        newy, newx = getnewpos(x, y, 1, direction)
        if height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0 and [newy, newx] not in coord:
            newcoord.append([newy, newx])
            newy, newx = getnewpos(x, y, speed - 1, direction)
            if speed > 1 and height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0 and [newy,
                                                                                                      newx] not in coord:
                newcoord0 = newcoord[:]
                newcoord0.append([newy, newx])
                ebene[depth][action] += wert
                q.put((checkchoices, [newx, newy, direction, board, speed - 1, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, action, newcoord0, [], 1]))
            newy, newx = getnewpos(x, y, speed, direction)
            if height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0 and [newy, newx] not in coord:
                newcoord1 = newcoord[:]
                newcoord1.append([newy, newx])
                ebene[depth][action] += wert
                q.put((checkchoices, [newx, newy, direction, board, speed, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, action, newcoord1, [], 2]))
            newy, newx = getnewpos(x, y, speed + 1, direction)
            if speed < 10 and height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0 and [newy,
                                                                                                       newx] not in coord:
                newcoord2 = newcoord[:]
                newcoord2.append([newy, newx])
                ebene[depth][action] += wert
                q.put((checkchoices, [newx, newy, direction, board, speed + 1, width, height, wert / 2,
                                      depth + 1, counter + 1, deadline, action, newcoord2, [], 0]))
    else:
        newy, newx = getnewpos(x, y, speed - 1, direction)
        if speed == 1:  # Sonderfall abfangen, sonst prüft aktuellen Kopf
            newy, newx = getnewpos(x, y, speed, direction)
        if height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0 and [newy, newx] not in coord:
            newcoord.append([newy, newx])
            hit = False
            for i in range(1, speed - 1):
                newyy, newxx = getnewpos(x, y, i, direction)
                if board[newyy][newxx] != 0 or [newyy, newxx] in coord:
                    hit = True
                    break
                newcoord.append([newyy, newxx])
            if not hit:
                if speed > 1:
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, direction, board, speed - 1, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, action, newcoord, [], 1]))
                newy, newx = getnewpos(x, y, speed, direction)
                if height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0 and [newy, newx] not in coord:
                    newcoord1 = newcoord[:]
                    newcoord1.append([newy, newx])
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, direction, board, speed, width, height, wert / 2,
                                          depth + 1, counter + 1, deadline, action, newcoord1, [], 2]))
                    newy, newx = getnewpos(x, y, speed + 1, direction)
                    if speed < 10 and height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0 and [newy,
                                                                                                               newx] not in coord:
                        newcoord2 = newcoord1[:]
                        newcoord2.append([newy, newx])
                        ebene[depth][action] += wert
                        q.put((checkchoices, [newx, newy, direction, board, speed + 1, width, height, wert / 2,
                                              depth + 1, counter + 1, deadline, action, newcoord2, [], 0]))

    # check-left
    newcoord3 = coord[:]
    newdirection = getnewdirection(direction, "left")
    newy, newx = getnewpos(x, y, speed, newdirection)
    if height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0 and [newy,
                                                                                newx] not in coord:
        hit = False
        newcoord3.append([newy, newx])
        for i in range(1, speed):
            if sprung:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                newyy, newxx = getnewpos(x, y, 1, newdirection)
                if board[newyy][newxx] != 0 or [newyy, newxx] in coord:
                    hit = True
                    break
                newcoord3.append([newyy, newxx])
                break
            newyy, newxx = getnewpos(x, y, i, newdirection)
            if board[newyy][newxx] != 0 or [newyy, newxx] in coord:
                hit = True
                break
            newcoord3.append([newyy, newxx])
        if not hit:
            ebene[depth][action] += wert
            q.put((checkchoices, [newx, newy, newdirection, board, speed, width, height, wert / 2,
                                  depth + 1, counter + 1, deadline, action, newcoord3, [], 3]))

    # check-right
    newcoord4 = coord[:]
    newdirection = getnewdirection(direction, "right")
    newy, newx = getnewpos(x, y, speed, newdirection)
    if height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0 and [newy,
                                                                                newx] not in coord:
        hit = False
        newcoord4.append([newy, newx])
        for i in range(1, speed):
            if sprung:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                newyy, newxx = getnewpos(x, y, 1, newdirection)
                if board[newyy][newxx] != 0 or [newyy, newxx] in coord:
                    hit = True
                    break
                newcoord4.append([newyy, newxx])
                break
            newyy, newxx = getnewpos(x, y, i, newdirection)
            if board[newyy][newxx] != 0 or [newyy, newxx] in coord:
                hit = True
                break
            newcoord4.append([newyy, newxx])
        if not hit:
            ebene[depth][action] += wert
            q.put((checkchoices, [newx, newy, newdirection, board, speed, width, height, wert / 2,
                                  depth + 1, counter + 1, deadline, action, newcoord4, [], 4]))


async def play():
    global ebene
    global q
    global myc
    global notbremse
    filename = 'apikey.txt'
    url = "wss://msoll.de/spe_ed"
    key = open(filename, "r").read().strip()
    async with websockets.connect(f"{url}?key={key}") as websocket:
        print("Waiting for initial state...", flush=True)
        counter = 0
        choices_actions = ["speed_up", "slow_down", "change_nothing", "turn_left", "turn_right"]
        wert = 1
        show = True  # Bestimmt, ob das GUI angezeigt wird

        while True:
            state_json = await websocket.recv()
            state = json.loads(state_json)
            print("<", state)
            print("Startzeit: " + str(datetime.utcnow()))
            own_player = state["players"][str(state["you"])]
            if not state["running"] or not own_player["active"]:
                if not own_player["active"]:
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
            myc = 0
            sprung = False
            depth = 0
            counter += 1
            if counter % 6 == 0:
                sprung = True
            choices = [0, 0, 0, 0, 0]
            ebene = [[0, 0, 0, 0, 0]]
            q = Queue()
            notbremse = False
            deadline = dp.parse(state["deadline"]).timestamp()
            coord0 = []
            coord1 = []
            coord2 = []
            coord3 = []
            coord4 = []

            # Prüfe Abstand nach Vorne, Links und Rechts
            vorne = distanz(state, own_player["direction"])
            links = distanz(state, getnewdirection(own_player["direction"], "left"))
            rechts = distanz(state, getnewdirection(own_player["direction"], "right"))

            # Erstelle ein Board mit allen möglichen Zügen der aktiven Gegner, um Überschneidungen im nächsten Schritt
            # zu verhindern. Berücksichtigt alle Züge, bei denen der Gegner nicht außerhalb des Feldes landet
            board = gegnerboard(state, sprung)

            # check sd,cn, su
            # Vorgehen: Bei Sprung prüfe erst gemeinsamen Schwanz, dann jeweils Kopf
            # Vorgehen: Bei nicht-Sprung prüfe sd komplett, dann Kopf cn, dann Kopf su
            if sprung:
                newy, newx = getnewpos(own_player["x"], own_player["y"], 1, own_player["direction"])
                if state["height"] > newy >= 0 and state["width"] > newx >= 0 and board[newy][newx] == 0:
                    coord0.append([newy, newx])
                    coord1.append([newy, newx])
                    coord2.append([newy, newx])
                    newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"] - 1,
                                           own_player["direction"])
                    if own_player["speed"] > 1 and state["height"] > newy >= 0 and state["width"] > newx >= 0 and \
                            board[newy][newx] == 0:
                        coord0.append([newy, newx])
                        ebene[depth][1] += wert
                        q.put((checkdistance, [newx, newy, own_player["direction"], board,
                                               own_player["speed"] - 1, state["width"],
                                               state["height"], wert / 2, depth + 1, counter + 1, deadline, 1, coord0,
                                               [], 1, vorne - (own_player["speed"] - 1)]))
                    newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"],
                                           own_player["direction"])
                    if state["height"] > newy >= 0 and state["width"] > newx >= 0 and board[newy][newx] == 0:
                        coord1.append([newy, newx])
                        ebene[depth][2] += wert
                        q.put((checkdistance, [newx, newy, own_player["direction"], board,
                                               own_player["speed"], state["width"], state["height"], wert / 2,
                                               depth + 1, counter + 1, deadline, 2, coord1, [], 2,
                                               vorne - own_player["speed"]]))
                    newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"] + 1,
                                           own_player["direction"])
                    if own_player["speed"] < 10 and state["height"] > newy >= 0 and state["width"] > newx >= 0 and \
                            board[newy][newx] == 0:
                        coord2.append([newy, newx])
                        ebene[depth][0] += wert
                        q.put((checkdistance, [newx, newy, own_player["direction"],
                                               board, own_player["speed"] + 1, state["width"],
                                               state["height"], wert / 2, depth + 1, counter + 1, deadline, 0, coord2,
                                               [], 0, vorne - (own_player["speed"] + 1)]))
            else:
                newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"] - 1,
                                       own_player["direction"])
                if own_player["speed"] == 1:  # Sonderfall abfangen, sonst prüft aktuellen Kopf
                    newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"],
                                           own_player["direction"])
                # Prüfe ob er das Spielfeld verlassen würde und ob Schlange an den neuen Stelle sind
                if state["height"] > newy >= 0 and state["width"] > newx >= 0 and board[newy][newx] == 0:
                    hit = False
                    coord0.append([newy, newx])
                    coord1.append([newy, newx])
                    coord2.append([newy, newx])
                    for i in range(1, own_player["speed"] - 1):
                        newyy, newxx = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        coord0.append([newyy, newxx])
                        coord1.append([newyy, newxx])
                        coord2.append([newyy, newxx])
                    if not hit:
                        if own_player["speed"] > 1:
                            ebene[depth][1] += wert
                            q.put((checkdistance, [newx, newy, own_player["direction"], board,
                                                   own_player["speed"] - 1, state["width"],
                                                   state["height"], wert / 2, depth + 1, counter + 1, deadline, 1,
                                                   coord0,
                                                   [], 1, vorne - (own_player["speed"] - 1)]))
                        newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"],
                                               own_player["direction"])
                        if state["height"] > newy >= 0 and state["width"] > newx >= 0 and board[newy][newx] == 0:
                            coord1.append([newy, newx])
                            coord2.append([newy, newx])
                            ebene[depth][2] += wert
                            q.put((checkdistance, [newx, newy, own_player["direction"], board,
                                                   own_player["speed"], state["width"], state["height"], wert / 2,
                                                   depth + 1, counter + 1, deadline, 2, coord1, [], 2,
                                                   vorne - own_player["speed"]]))
                            newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"] + 1,
                                                   own_player["direction"])
                            if own_player["speed"] < 10 and state["height"] > newy >= 0 and state[
                                "width"] > newx >= 0 and \
                                    board[newy][newx] == 0:
                                coord2.append([newy, newx])
                                ebene[depth][0] += wert
                                q.put((checkdistance, [newx, newy, own_player["direction"],
                                                       board, own_player["speed"] + 1, state["width"],
                                                       state["height"], wert / 2, depth + 1, counter + 1, deadline, 0,
                                                       coord2,
                                                       [], 0, vorne - (own_player["speed"] + 1)]))

            # check-left
            newdirection = getnewdirection(own_player["direction"], "left")
            newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"], newdirection)
            # Prüfe ob er das Spielfeld verlassen würde, ob Schlange an den neuen Stelle sind
            if state["height"] > newy >= 0 and state["width"] > newx >= 0 and board[newy][newx] == 0:
                hit = False
                coord3.append([newy, newx])
                for i in range(1, own_player["speed"]):
                    if sprung:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newyy, newxx = getnewpos(own_player["x"], own_player["y"], 1, newdirection)
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        coord3.append([newyy, newxx])
                        break
                    newyy, newxx = getnewpos(own_player["x"], own_player["y"], i, newdirection)
                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    coord3.append([newyy, newxx])
                if not hit:
                    ebene[depth][3] += wert
                    q.put((checkdistance, [newx, newy, newdirection, board,
                                           own_player["speed"], state["width"], state["height"],
                                           wert / 2, depth + 1, counter + 1, deadline, 3, coord3, [], 3,
                                           links - own_player["speed"]]))

            # check-right
            newdirection = getnewdirection(own_player["direction"], "right")
            newy, newx = getnewpos(own_player["x"], own_player["y"], own_player["speed"], newdirection)
            # Prüfe ob er das Spielfeld verlassen würde, ob Schlange an den neuen Stelle sind
            if state["height"] > newy >= 0 and state["width"] > newx >= 0 and board[newy][newx] == 0:
                hit = False
                coord4.append([newy, newx])
                for i in range(1, own_player["speed"]):
                    if sprung:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newyy, newxx = getnewpos(own_player["x"], own_player["y"], 1, newdirection)
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        coord4.append([newyy, newxx])
                        break
                    newyy, newxx = getnewpos(own_player["x"], own_player["y"], i, newdirection)
                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    coord4.append([newyy, newxx])
                if not hit:
                    ebene[depth][4] += wert
                    q.put((checkdistance, [newx, newy, newdirection, board,
                                           own_player["speed"], state["width"], state["height"],
                                           wert / 2, depth + 1, counter + 1, deadline, 4, coord4, [], 4,
                                           rechts - own_player["speed"]]))

            # Bearbeite solange Objekte aus der Queue bis diese leer ist oder 1 Sekunde bis zur Deadline verbleibt
            while not q.empty() and not notbremse:
                f, args = q.get()
                f(*args)

            # Züge, die tiefere Ebenen erreichen, werden deutlich bevorzugt (+100)
            print(ebene)
            for i in range(0, 5):
                if myc > 0:
                    if ebene[myc - 1][i] != 0:
                        ebene[0][i] += 10000

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
            action_json = json.dumps({"action": action})
            if show:  # GUI, falls show == True
                anzeige(state, counter, action, choices, myc - 1)
            await websocket.send(action_json)


asyncio.get_event_loop().run_until_complete(play())
