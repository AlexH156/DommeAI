#!/usr/bin/env python3

import asyncio
import random
from datetime import datetime
import json
from queue import Queue

import websockets
from copy import deepcopy

# TODO / Ideen : Prüfung, ob nächster Zug "einsperrt"
# TODO alles optimieren->höhere Tiefe möglich
# TODO / Ideen : Aktuell bevorzugt er nach vorne gehen gegenüber abbiegen, weil bei geradeaus hat er noch die
#   Möglichkeiten sd,cn und su
# TODO: teilweise berechnete Ebenen mit Durchschnitt berechnen lassen
# TODO / Ideen: Evtl. in den letzten 5 sek z.B. keine Methode mehr in die Queue
            #Vielleicht die Tiefe bevorzugen, dann erst die möglichen Richtungen

global ebene
global notbremse
global q


def getnewdirection(dir, change):  # bestimme neue Richtung nach Wechsel
    if dir == change:
        return "down"
    if change == "left":
        if dir == "up":
            return "left"
        elif dir == "down":
            return "right"
        else:
            return "up"
    else:
        if dir == "down":
            return "left"
        elif dir == "up":
            return "right"
        else:
            return "up"


def getnewpos(x, y, s, dir):  # bestimme neue Position
    if dir == "up":
        return [y - s, x]
    elif dir == "down":
        return [y + s, x]
    elif dir == "left":
        return [y, x - s]
    else:
        return [y, x + s]


def checkchoices(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action):
    global ebene
    global q
    global notbremse

    if not len(ebene) > depth:
        ebene.append([0,0,0,0,0])

    #   Bei Jahreswechsel kann es zu Fehlern (zu kurzen Berechnungen) kommen..
    #   Auch so kann es sein, dass die ersten Berechnungen noch durchkommen, der Rest aber nicht mehr

    current_time = str(datetime.utcnow())
    mo = int(current_time[5:7])
    t = int(current_time[8:10])
    h = int(current_time[11:13])
    m = int(current_time[14:16])
    s = int(current_time[17:19])
    ctime = (((mo*30+t)*24+h)*60+m)*60+s

    if ctime+1 > deadline:
        ebene[depth][action] = -2
        notbremse = True
        print(depth)
        return

    clearsd = False     #wird verwendet, um Ressourcen bei CN zu schonen (CN = SD mit neuem Kopf). Also wenn True, dann muss nurnoch Kopf geprüft werden
    clearcn = False     #wird verwendet, um Ressourcen bei SU zu schonen (CU = CN mit neuem Kopf). Also wenn True, dann muss nurnoch Kopf geprüft werden

    # check-slowdown
    newboard = deepcopy(board)
    if speed > 1:
        newpos = getnewpos(x, y, speed - 1, direction)
        newx = newpos[1]
        newy = newpos[0]
        if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                newboard[newy][newx] = 7
                hit = False
                for i in range(1, speed - 1):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newpos = getnewpos(x, y, 1, direction)
                        newxx = newpos[1]
                        newyy = newpos[0]
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        newboard[newyy][newxx] = 7
                        break
                    newpos = getnewpos(x, y, i, direction)
                    newxx = newpos[1]
                    newyy = newpos[0]

                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                if not hit:
                    clearsd = True
                    ebene[depth][action] += wert
                    q.put((checkchoices,[newx, newy, direction, newboard, speed - 1, width, height, wert / 2,
                                               depth + 1, counter + 1, deadline, action]))

    # check-nothing
    if not clearsd:
        newboard = deepcopy(board)
    newpos = getnewpos(x, y, speed, direction)
    newx = newpos[1]
    newy = newpos[0]
    if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
        if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
            newboard[newy][newx] = 7
            hit = False
            for i in range(1, speed):
                if clearsd:
                    break
                if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                    newpos = getnewpos(x, y, 1, direction)
                    newxx = newpos[1]
                    newyy = newpos[0]
                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                    break
                newpos = getnewpos(x, y, i, direction)
                newxx = newpos[1]
                newyy = newpos[0]

                if not board[newyy][newxx] == 0:
                    hit = True
                    break
                newboard[newyy][newxx] = 7
            if not hit:
                clearcn = True
                ebene[depth][action] += wert
                q.put((checkchoices,[newx, newy, direction, newboard, speed, width, height, wert / 2,
                                           depth + 1, counter + 1, deadline,action]))

    # check-speedup
    if not clearcn:
        newboard = deepcopy(board)
    if speed < 10:
        newpos = getnewpos(x, y, speed + 1, direction)
        newx = newpos[1]
        newy = newpos[0]
        if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                hit = False
                newboard[newy][newx] = 7
                for i in range(1, speed + 1):
                    if clearcn:
                        break
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newpos = getnewpos(x, y, 1, direction)
                        newxx = newpos[1]
                        newyy = newpos[0]
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        newboard[newyy][newxx] = 7
                        break
                    newpos = getnewpos(x, y, i, direction)
                    newxx = newpos[1]
                    newyy = newpos[0]

                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7  # TODO evtl anpassen, dass mit SpielerID geschrieben wird, aber irrelevant
                if not hit:
                    ebene[depth][action] += wert
                    q.put((checkchoices,[newx, newy, direction, newboard, speed + 1, width, height, wert / 2,
                                               depth + 1, counter + 1, deadline,action]))

    # check-left and check-right
    for newd in ["left", "right"]:
        newboard = deepcopy(board)
        newdirection = getnewdirection(direction, newd)
        newpos = getnewpos(x, y, speed, newdirection)
        newx = newpos[1]
        newy = newpos[0]
        if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                newboard[newy][newx] = 7
                hit = False
                for i in range(1, speed):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newpos = getnewpos(x, y, 1, newdirection)
                        newxx = newpos[1]
                        newyy = newpos[0]
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        newboard[newyy][newxx] = 7
                        break
                    newpos = getnewpos(x, y, i, newdirection)
                    newxx = newpos[1]
                    newyy = newpos[0]

                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                if not hit:
                    ebene[depth][action] += wert
                    q.put((checkchoices,[newx, newy, newdirection, newboard, speed, width, height, wert / 2,
                                               depth + 1, counter + 1, deadline,action]))



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
            print("Startzeit: " + str(datetime.utcnow()))
            own_player = state["players"][str(state["you"])]
            if not state["running"] or not own_player["active"]:
                if not own_player["active"]:
                    erfolg = "verloren"
                else:
                    valid_responses = ["Winner Winner, Chicken Dinner", "git gud", "Too weak, too slow", "ez game, ez life", "ez pz lemon squeezy", "ez", "rekt", "l2p", "noobs", "too ez"]
                    erfolg = random.choice(valid_responses)
                print(erfolg)
                break
            depth = 0
            counter += 1
            choices = [0, 0, 0, 0, 0]
            global ebene
            ebene = [[0,0,0,0,0]]
            global q
            q = Queue()

            clearsd = False
            clearcn = False
            mo = int(state["deadline"][5:7])
            t = int(state["deadline"][8:10])
            h = int(state["deadline"][11:13])
            m = int(state["deadline"][14:16])
            s = int(state["deadline"][17:19])
            deadline = (((mo * 30 + t) * 24 + h) * 60 + m) * 60 + s


            # Noch nicht alles perfekt. Prüft nicht ob sechste runde und ob er in sich selbst rein crashen würde.
            # Würde es aus performancegründen auch nicht reinbringen (so bleibt unsere Schlange sehr defensiv)
            boardenemies = deepcopy(state["cells"])
            #   Gehe durch alle Spieler die noch aktiv sind
            for p in range(1, int(len(state["players"]) + 1)):
                if state["players"][str(p)]["active"]:
                    if not state["you"] == p:

                        #   Prüfe erst ob bei Verlangsamung überleben würde, trage ein, dann CN prüfen und eintragen,
                        #   als letztes Beschleinigung prüfen und eintragen (Beachte nicht Sonderfall der 6.ten Runde
                        pnewpos = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                            state["players"][str(p)]["speed"] - 1, state["players"][str(p)]["direction"])
                        pnewx = pnewpos[1]
                        pnewy = pnewpos[0]
                        # Prüfe ob er das Spielfeld verlassen würde, wenn verlangsamt
                        if state["height"] - 1 >= pnewy >= 0 and state["width"] - 1 >= pnewx >= 0:
                            boardenemies[pnewy][pnewx] = 7
                            for i in range(1, state["players"][str(p)]["speed"] - 1):
                                pnewpos = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                    i, state["players"][str(p)]["direction"])
                                pnewx = pnewpos[1]
                                pnewy = pnewpos[0]
                                boardenemies[pnewy][pnewx] = 7
                            pnewpos = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                state["players"][str(p)]["speed"], state["players"][str(p)]["direction"])
                            pnewx = pnewpos[1]
                            pnewy = pnewpos[0]
                            # Prüfe ob er das Spielfeld verlassen würde, wenn nichts macht
                            if state["height"] - 1 >= pnewy >= 0 and state["width"] - 1 >= pnewx >= 0:
                                boardenemies[pnewy][pnewx] = 7
                                pnewpos = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                    state["players"][str(p)]["speed"] + 1,
                                                    state["players"][str(p)]["direction"])
                                pnewx = pnewpos[1]
                                pnewy = pnewpos[0]
                                # Prüfe ob er das Spielfeld verlassen würde, wenn beschleunigt
                                if state["height"] - 1 >= pnewy >= 0 and state["width"] - 1 >= pnewx >= 0:
                                    boardenemies[pnewy][pnewx] = 7

                        # Prüfe ob bei links/rechts außerhalb des Spielfeldes, sonst trage ein
                        for newd in ["left", "right"]:
                            newdirection = getnewdirection(state["players"][str(p)]["direction"], newd)
                            pnewpos = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                state["players"][str(p)]["speed"], newdirection)
                            pnewx = pnewpos[1]
                            pnewy = pnewpos[0]
                            # Prüfe ob er das Spielfeld verlassen würde, wenn links/rechts
                            if state["height"] - 1 >= pnewy >= 0 and state["width"] - 1 >= pnewx >= 0:
                                boardenemies[pnewy][pnewx] = 7
                                for i in range(1, state["players"][str(p)]["speed"]):
                                    pnewpos = getnewpos(state["players"][str(p)]["x"], state["players"][str(p)]["y"],
                                                        i, newdirection)
                                    pnewx = pnewpos[1]
                                    pnewy = pnewpos[0]
                                    boardenemies[pnewy][pnewx] = 7
            #print(boardenemies)


            # check-slowdown
            board = deepcopy(boardenemies)
            if own_player["speed"] > 1:
                newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"] - 1, own_player["direction"])
                newx = newpos[1]
                newy = newpos[0]
                # Prüfe ob er das Spielfeld verlassen würde
                if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
                    if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                        board[newy][newx] = 7
                        hit = False
                        for i in range(1, own_player["speed"] - 1):
                            if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                                newpos = getnewpos(own_player["x"], own_player["y"], 1, own_player["direction"])
                                newxx = newpos[1]
                                newyy = newpos[0]
                                if not state["cells"][newyy][newxx] == 0:
                                    hit = True
                                    break
                                board[newyy][newxx] = 7
                                break
                            newpos = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                            newxx = newpos[1]
                            newyy = newpos[0]
                            if not state["cells"][newyy][newxx] == 0:
                                hit = True
                                break
                            board[newyy][newxx] = 7
                        if not hit:
                            clearsd = True
                            #print("sd: " + str(newx) + " " + str(newy))
                            ebene[depth][1] += wert
                            q.put((checkchoices,[newx, newy, own_player["direction"], board,
                                                             own_player["speed"] - 1, state["width"],
                                                             state["height"], wert / 2, depth+1, counter + 1, deadline,1]))

            # check-nothing
            if not clearsd:
                board = deepcopy(boardenemies)
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"], own_player["direction"])
            newx = newpos[1]
            newy = newpos[0]
            # Prüfe ob er das Spielfeld verlassen würde
            if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                    board[newy][newx] = 7
                    hit = False
                    for i in range(1, own_player["speed"]):
                        if clearsd:
                            break
                        if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                            newpos = getnewpos(own_player["x"], own_player["y"], 1, own_player["direction"])
                            newxx = newpos[1]
                            newyy = newpos[0]
                            if not state["cells"][newyy][newxx] == 0:
                                hit = True
                                break
                            board[newyy][newxx] = 7
                            break
                        newpos = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                        newxx = newpos[1]
                        newyy = newpos[0]
                        if not state["cells"][newyy][newxx] == 0:
                            hit = True
                            break
                        board[newyy][newxx] = 7
                    if not hit:
                        clearcn = True
                        #print("cn: " + str(newx) + " " + str(newy))
                        ebene[depth][2] += wert
                        q.put((checkchoices,[newx, newy, own_player["direction"], board,
                                                         own_player["speed"], state["width"], state["height"], wert / 2,
                                                         depth+1, counter + 1, deadline,2]))

            # check-speedup
            if not clearcn:
                board = deepcopy(boardenemies)
            if own_player["speed"] < 10:
                newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"] + 1, own_player["direction"])
                newx = newpos[1]
                newy = newpos[0]
                # Prüfe ob er das Spielfeld verlassen würde
                if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
                    if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                        board[newy][newx] = 7
                        hit = False
                        for i in range(1, own_player["speed"] + 1):
                            if clearcn:
                                break
                            if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                                newpos = getnewpos(own_player["x"], own_player["y"], 1, own_player["direction"])
                                newxx = newpos[1]
                                newyy = newpos[0]
                                if not state["cells"][newyy][newxx] == 0:
                                    hit = True
                                    break
                                board[newyy][newxx] = 7
                                break
                            newpos = getnewpos(own_player["x"], own_player["y"], i, own_player["direction"])
                            newxx = newpos[1]
                            newyy = newpos[0]
                            if not state["cells"][newyy][newxx] == 0:
                                hit = True
                                break
                            board[newyy][newxx] = 7

                        if not hit:
                            #print("su: " + str(newx) + " " + str(newy))
                            ebene[depth][0] += wert
                            q.put((checkchoices,[newx, newy, own_player["direction"],
                                                             board, own_player["speed"] + 1, state["width"],
                                                             state["height"], wert / 2, depth+1, counter + 1, deadline,0]))

            # check-left
            board = deepcopy(boardenemies)
            newdirection = getnewdirection(own_player["direction"], "left")
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"], newdirection)
            newx = newpos[1]
            newy = newpos[0]
            # Prüfe ob er das Spielfeld verlassen würde
            if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                    board[newy][newx] = 7
                    hit = False
                    for i in range(1, own_player["speed"]):
                        if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                            newpos = getnewpos(own_player["x"], own_player["y"], 1, newdirection)
                            newxx = newpos[1]
                            newyy = newpos[0]
                            if not state["cells"][newyy][newxx] == 0:
                                hit = True
                                break
                            board[newyy][newxx] = 7
                            break
                        newpos = getnewpos(own_player["x"], own_player["y"], i, newdirection)
                        newxx = newpos[1]
                        newyy = newpos[0]
                        if not state["cells"][newyy][newxx] == 0:
                            hit = True
                            break
                        board[newyy][newxx] = 7
                    if not hit:
                        #print("l: " + str(newx) + " " + str(newy))
                        ebene[depth][3] += wert
                        q.put((checkchoices,[newx, newy, newdirection, board,
                                                         own_player["speed"], state["width"], state["height"],
                                                         wert / 2, depth+1, counter + 1, deadline,3]))

            # check-right
            board = deepcopy(boardenemies)
            newdirection = getnewdirection(own_player["direction"], "right")
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"], newdirection)
            newx = newpos[1]
            newy = newpos[0]
            # Prüfe ob er das Spielfeld verlassen würde
            if state["height"] - 1 >= newy >= 0 and state["width"] - 1 >= newx >= 0:
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                    board[newy][newx] = 7
                    hit = False
                    for i in range(1, own_player["speed"]):
                        if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                            newpos = getnewpos(own_player["x"], own_player["y"], 1, newdirection)
                            newxx = newpos[1]
                            newyy = newpos[0]
                            if not state["cells"][newyy][newxx] == 0:
                                hit = True
                                break
                            board[newyy][newxx] = 7
                            break
                        newpos = getnewpos(own_player["x"], own_player["y"], i, newdirection)
                        newxx = newpos[1]
                        newyy = newpos[0]
                        if not state["cells"][newyy][newxx] == 0:
                            hit = True
                            break
                        board[newyy][newxx] = 7
                    if not hit:
                        #print("r: " + str(newx) + " " + str(newy))
                        ebene[depth][4] += wert
                        q.put((checkchoices,[newx, newy, newdirection, board,
                                                         own_player["speed"], state["width"], state["height"],
                                                         wert / 2, depth+1, counter + 1, deadline,4]))

            global notbremse
            notbremse = False
            while not q.empty():
                f, args = q.get()
                f(*args)
                if notbremse:
                    break

            # zusammenrechnen
            myc = -1
            bremse = False
            while True:
                myc += 1
                for i in range(0, 5):
                    if ebene[myc][i] < 0:
                        bremse = True
                        break
                if bremse:
                    break

            for i in range(0, myc):
                for j in range(0, 5):
                    choices[j] += ebene[i][j]

            # Wähle von den möglichen Zügen den bestbewertesten (also welcher die meisten Unterzüge ermöglicht) aus
            # und gebe diesen aus. Falls 2 Züge gleich gut sind, dann wähle zufällig einen aus
            print(choices)
            best = max(choices)
            #print(state["deadline"])
            action = choices_actions[choices.index(best)]
            randy = []
            for i in range(len(choices)):
                if choices[i] == best:
                    randy.append(choices_actions[i])
            if len(randy) > 1:
                # print("random")
                action = random.choice(randy)
            print("Endzeit: " + str(datetime.utcnow()))
            print(">", action)
            action_json = json.dumps({"action": action})
            await websocket.send(action_json)


asyncio.get_event_loop().run_until_complete(play())
