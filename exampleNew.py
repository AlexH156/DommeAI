#!/usr/bin/env python3

import asyncio
import random
import time
from datetime import datetime
import json
import websockets
from copy import copy, deepcopy

def getnewdirection(dir, change):  # bestimme neue Richtung nach Wechsel
    if (dir == "up") and (change == "left"):
        return "left"
    elif (dir == "down") and (change == "left"):
        return "right"
    elif (dir == "right") and (change == "left"):
        return "up"
    elif (dir == "left") and (change == "left"):
        return "down"
    elif (dir == "down") and (change == "right"):
        return "left"
    elif (dir == "up") and (change == "right"):
        return "right"
    elif (dir == "left") and (change == "right"):
        return "up"
    elif (dir == "right") and (change == "right"):
        return "down"


def getnewpos(x, y, s, dir):  # bestimme neue Position
    if dir == "up":
        return [y - s, x]
    elif dir == "down":
        return [y + s, x]
    elif dir == "left":
        return [y, x - s]
    elif dir == "right":
        return [y, x + s]


def checkchoices(x, y, direction, board, speed, width, height, wert, depth, counter):
    sum = 0

    if depth <= 0:
        return 0



    # check-speedup
    newboard = deepcopy(board)
    if speed < 10:
        newpos = getnewpos(x, y, speed + 1, direction)
        newx = newpos[1]
        newy = newpos[0]
        if height - 1 >= newy and width - 1 >= newx and (newx >= 0) and (
                newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                hilfe = 0
                newboard[newy][newx] = 1
                for i in range(1, speed + 1):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                        i = 1
                    newpos = getnewpos(x, y, i, direction)
                    newx = newpos[1]
                    newy = newpos[0]

                    if not board[newy][newx] == 0:
                        hilfe = 1
                    newboard[newy][newx] = 1  # TODO evtl anpassen, dass mit SpielerID geschrieben wird
                if hilfe == 0:
                    sum += wert + checkchoices(newx, newy, direction, newboard, speed + 1, width, height, wert / 2,
                                               depth - 1, counter + 1)

    # check-slowdown
    newboard = deepcopy(board)
    if speed > 1:
        newpos = getnewpos(x, y, speed - 1, direction)
        newx = newpos[1]
        newy = newpos[0]
        if height - 1 >= newy and width - 1 >= newx and (newx >= 0) and (
                newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                newboard[newy][newx] = 1
                if speed > 2:
                    hilfe = 0
                    for i in range(1, speed - 1):
                        if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                            i = 1
                        newpos = getnewpos(x, y, i,
                                           direction)
                        newx = newpos[1]
                        newy = newpos[0]

                        if not board[newy][newx] == 0:
                            hilfe = 1
                        newboard[newy][newx] = 1
                    if hilfe == 0:
                        sum += wert + checkchoices(newx, newy, direction, newboard, speed - 1, width, height, wert / 2,
                                                   depth - 1, counter + 1)
                else:
                    sum += wert + checkchoices(newx, newy, direction, newboard, speed - 1, width, height, wert / 2,
                                               depth - 1, counter + 1)

    # check-nothing
    newboard = deepcopy(board)
    newpos = getnewpos(x, y, speed, direction)
    newx = newpos[1]
    newy = newpos[0]
    if height - 1 >= newy and width - 1 >= newx and (newx >= 0) and (
            newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
        if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
            newboard[newy][newx] = 1
            if speed > 1:
                hilfe = 0
                for i in range(1, speed):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                        i = 1
                    newpos = getnewpos(x, y, i, direction)
                    newx = newpos[1]
                    newy = newpos[0]

                    if not board[newy][newx] == 0:
                        hilfe = 1
                    newboard[newy][newx] = 1
                if hilfe == 0:
                    sum += wert + checkchoices(newx, newy, direction, newboard, speed, width, height, wert / 2,
                                               depth - 1, counter + 1)
            else:
                sum += wert + checkchoices(newx, newy, direction, newboard, speed, width, height, wert / 2, depth - 1,
                                           counter + 1)

    # check-left
    newboard = deepcopy(board)
    newdirection = getnewdirection(direction, "left")
    newpos = getnewpos(x, y, speed, newdirection)
    newx = newpos[1]
    newy = newpos[0]
    if height - 1 >= newy and width - 1 >= newx and (newx >= 0) and (
            newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
        if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
            newboard[newy][newx] = 1
            if speed > 1:
                hilfe = 0
                for i in range(1, speed):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                        i = 1
                    newpos = getnewpos(x, y, i, newdirection)
                    newx = newpos[1]
                    newy = newpos[0]

                    if not board[newy][newx] == 0:
                        hilfe = 1
                    newboard[newy][newx] = 1
                if hilfe == 0:
                    sum += wert + checkchoices(newx, newy, newdirection, newboard, speed, width, height, wert / 2,
                                               depth - 1, counter + 1)
            else:
                sum += wert + checkchoices(newx, newy, newdirection, newboard, speed, width, height, wert / 2,
                                           depth - 1, counter + 1)

    # check-right
    newboard = deepcopy(board)
    newdirection = getnewdirection(direction, "right")
    newpos = getnewpos(x, y, speed, newdirection)
    newx = newpos[1]
    newy = newpos[0]
    if height - 1 >= newy and width - 1 >= newx and (newx >= 0) and (
            newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
        if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
            newboard[newy][newx] = 1
            if speed > 1:
                hilfe = 0
                for i in range(1, speed):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                        i = 1
                    newpos = getnewpos(x, y, i, newdirection)
                    newx = newpos[1]
                    newy = newpos[0]
                    if not board[newy][newx] == 0:
                        hilfe = 1
                    newboard[newy][newx] = 1
                if hilfe == 0:
                    sum += wert + checkchoices(newx, newy, newdirection, newboard, speed, width, height, wert / 2,
                                               depth - 1, counter + 1)
            else:
                sum += wert + checkchoices(newx, newy, newdirection, newboard, speed, width, height, wert / 2,
                                           depth - 1, counter + 1)
    return sum


async def play():
    filename = 'apikey.txt'

    url = "wss://msoll.de/spe_ed"
    key = open(filename, "r").read().strip()

    async with websockets.connect(f"{url}?key={key}") as websocket:
        print("Waiting for initial state...", flush=True)
        counter = 0
        choices_actions = ["speed_up", "slow_down", "change_nothing", "turn_left", "turn_right"]
        wert = 1

        while True:
            state_json = await websocket.recv()
            state = json.loads(state_json)
            print("<", state)
            print("Startzeit: " + str(datetime.now()))
            own_player = state["players"][str(state["you"])]
            if not state["running"] or not own_player["active"]:
                if not own_player["active"]:
                    erfolg = "verloren"
                else:
                    erfolg = "gewonnen"
                print(erfolg)
                break
            counter += 1
            choices = [0, 0, 0, 0, 0]


            # check-speedup
            board = deepcopy(state["cells"])
            if own_player["speed"] < 10:
                newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"] + 1, own_player["direction"])
                newx = newpos[1]
                newy = newpos[0]
                if state["height"] - 1 >= newy and state["width"] - 1 >= newx and (newx >= 0) and (newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                    if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                        board[newy][newx] = 1
                        hilfe = 0
                        for i in range(1, own_player["speed"] + 1):
                            if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke TODO (verschwenderisch)
                                i = 1
                            newpos = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                            newxx = newpos[1]
                            newyy = newpos[0]
                            if not state["cells"][newyy][newxx] == 0:
                                hilfe = 1
                                #break
                            board[newyy][newxx] = 1

                        if hilfe == 0:
                            choices[0] = wert + checkchoices(newx,newy, own_player["direction"],
                                                             board, own_player["speed"] + 1, state["width"],
                                                             state["height"], wert / 2, 5, counter + 1)

            # check-slowdown
            board = deepcopy(state["cells"])
            if own_player["speed"] > 1:
                newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"] - 1, own_player["direction"])
                newx = newpos[1]
                newy = newpos[0]
                if state["height"] - 1 >= newy and state["width"] - 1 >= newx and (newx >= 0) and (
                        newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                    if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                        board[newy][newx] = 1
                        if own_player["speed"] > 2:
                            hilfe = 0
                            for i in range(1, own_player["speed"] - 1):
                                if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                                    i = 1
                                newpos = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                                newxx = newpos[1]
                                newyy = newpos[0]
                                if not state["cells"][newyy][newxx] == 0:
                                    hilfe = 1
                                    #break
                                board[newyy][newxx] = 1
                            if hilfe == 0:
                                choices[1] = wert + checkchoices(newx,newy, own_player["direction"], board,
                                                                 own_player["speed"] - 1, state["width"],
                                                                 state["height"], wert / 2, 5, counter + 1)
                        else:
                            choices[1] = wert + checkchoices(newx,newy, own_player["direction"],
                                                             board, own_player["speed"] - 1, state["width"],
                                                             state["height"], wert / 2, 5, counter + 1)

            # check-nothing
            board = deepcopy(state["cells"])
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"], own_player["direction"])
            newx = newpos[1]
            newy = newpos[0]
            if state["height"] - 1 >= newy and state["width"] - 1 >= newx and (newx >= 0) and (newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                    board[newy][newx] = 1
                    if own_player["speed"] > 1:
                        hilfe = 0
                        for i in range(1, own_player["speed"]):
                            if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                                i = 1
                            newpos = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                            newxx = newpos[1]
                            newyy = newpos[0]
                            if not state["cells"][newyy][newxx] == 0:
                                hilfe = 1
                                #break
                            board[newyy][newxx] = 1
                        if hilfe == 0:
                            choices[2] = wert + checkchoices(newx,newy, own_player["direction"], board, own_player["speed"], state["width"], state["height"], wert / 2, 5, counter + 1)
                    else:
                        choices[2] = wert + checkchoices(newx,newy, own_player["direction"], board, own_player["speed"], state["width"], state["height"], wert / 2, 5, counter + 1)

            # check-left
            board = deepcopy(state["cells"])
            newdirection = getnewdirection(own_player["direction"], "left")
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"], newdirection)
            newx = newpos[1]
            newy = newpos[0]
            if state["height"] - 1 >= newy and state["width"] - 1 >= newx and (newx >= 0) and (
                    newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                    board[newy][newx] = 1
                    if own_player["speed"] > 1:
                        hilfe = 0
                        for i in range(1, own_player["speed"]):
                            if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                                i = 1
                            newpos = getnewpos(own_player["x"], own_player["y"], i, newdirection)
                            newxx = newpos[1]
                            newyy = newpos[0]
                            if not state["cells"][newyy][newxx] == 0:
                                hilfe = 1
                                #break
                            board[newyy][newxx] = 1
                        if hilfe == 0:
                            choices[3] = wert + checkchoices(newx,newy, newdirection, board,
                                                             own_player["speed"], state["width"], state["height"],
                                                             wert / 2, 5, counter + 1)
                    else:
                        choices[3] = wert + checkchoices(newx,newy, newdirection, board,
                                                         own_player["speed"], state["width"], state["height"], wert / 2,
                                                         5, counter + 1)

            # check-right
            board = deepcopy(state["cells"])
            newdirection = getnewdirection(own_player["direction"], "right")
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"], newdirection)
            newx = newpos[1]
            newy = newpos[0]
            if state["height"] - 1 >= newy and state["width"] - 1 >= newx and (newx >= 0) and (
                    newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                    board[newy][newx] = 1
                    if own_player["speed"] > 1:
                        hilfe = 0
                        for i in range(1, own_player["speed"]):
                            if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                                i = 1
                            newpos = getnewpos(own_player["x"], own_player["y"], i,newdirection)
                            newxx = newpos[1]
                            newyy = newpos[0]
                            if not state["cells"][newyy][newxx] == 0:
                                hilfe = 1
                                #break
                            board[newyy][newxx] = 1
                        if hilfe == 0:
                            choices[4] = wert + checkchoices(newx,newy, newdirection, board,
                                                             own_player["speed"], state["width"], state["height"],
                                                             wert / 2, 5, counter + 1)
                    else:
                        choices[4] = wert + checkchoices(newx,newy, newdirection, board,
                                                         own_player["speed"], state["width"], state["height"], wert / 2,
                                                         5, counter + 1)
            #time.sleep(4)
            print(choices)
            best = max(choices)
            #print(best)
            action = choices_actions[choices.index(best)]
            randy = []
            for i in range(len(choices)):
                if choices[i] == best:
                    randy.append(choices_actions[i])
            if len(randy) > 1:
                print("random")
                action = random.choice(randy)
            print("Endzeit: " + str(datetime.now()))
            print(">", action)
            action_json = json.dumps({"action": action})
            await websocket.send(action_json)


asyncio.get_event_loop().run_until_complete(play())



