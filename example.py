#!/usr/bin/env python3

import asyncio
import json
import os
import random
import websockets

def getnewdirection(dir, change):  # bestimme neue Richtung nach Wechsel
    if (dir == "up") & (change == "left"):
        return "left"
    elif (dir == "down") & (change == "left"):
        return "right"
    elif (dir == "right") & (change == "left"):
        return "up"
    elif (dir == "left") & (change == "left"):
        return "down"
    elif (dir == "down") & (change == "right"):
        return "left"
    elif (dir == "up") & (change == "right"):
        return "right"
    elif (dir == "left") & (change == "right"):
        return "up"
    elif (dir == "right") & (change == "right"):
        return "down"


def getnewpos(x, y, s, dir):  # bestimme neue Position
    if dir == "up":
        return [y - s,x]
    elif dir == "down":
        return [y + s,x]
    elif dir == "left":
        return [y, x - s]
    elif dir == "right":
        return [y, x + s]

async def play():
    url = os.environ["URL"]
    key = os.environ["KEY"]

    async with websockets.connect(f"{url}?key={key}") as websocket:
        print("Waiting for initial state...", flush=True)
        counter = 0
        while True:
            state_json = await websocket.recv()
            state = json.loads(state_json)
            print("<", state)
            own_player = state["players"][str(state["you"])]
            if not state["running"] or not own_player["active"]:
                break
            valid_actions = []
            counter += 1

            #check-speedup
            if own_player["speed"] < 10:
                newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"]+1, own_player["direction"])
                newx = newpos[1]
                newy = newpos[0]
                if ([state["height"] - 1, state["width"] - 1] >= newpos) & (newx >= 0) & (newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                    if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                        hilfe = 0
                        for i in range(1,own_player["speed"]+1):
                            if counter % 6 == 0:         # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                                i = 1
                            newpos = getnewpos(own_player["x"], own_player["y"], i,
                                               own_player["direction"])
                            newx = newpos[1]
                            newy = newpos[0]
                            if not state["cells"][newy][newx] == 0:
                                hilfe = 1
                        if hilfe == 0:
                            valid_actions += ["speed_up"]


            #check-slowdown
            if own_player["speed"] > 1:
                newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"]-1, own_player["direction"])
                newx = newpos[1]
                newy = newpos[0]
                if ([state["height"] - 1, state["width"] - 1] >= newpos) & (newx >= 0) & (newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                    if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                        if own_player["speed"] > 2:
                            hilfe = 0
                            for i in range(1,own_player["speed"]-1):
                                if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                                    i = 1
                                newpos = getnewpos(own_player["x"], own_player["y"], i,
                                                   own_player["direction"])
                                newx = newpos[1]
                                newy = newpos[0]
                                if not state["cells"][newy][newx] == 0:
                                    hilfe = 1
                            if hilfe == 0:
                                valid_actions += ["slow_down"]
                        else:
                            valid_actions += ["slow_down"]

            # check-nothing
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"], own_player["direction"])
            newx = newpos[1]
            newy = newpos[0]
            if ([state["height"] - 1, state["width"] - 1] >= newpos) & (newx >= 0) & (
                    newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                    if own_player["speed"] > 1:
                        hilfe = 0
                        for i in range(1, own_player["speed"]):
                            if counter % 6 == 0:         # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                                i = 1
                            newpos = getnewpos(own_player["x"], own_player["y"], i,
                                               own_player["direction"])
                            newx = newpos[1]
                            newy = newpos[0]
                            if not state["cells"][newy][newx] == 0:
                                hilfe = 1
                        if hilfe == 0:
                            valid_actions += ["change_nothing"]
                    else:
                        valid_actions += ["change_nothing"]

            # check-left
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"],
                               getnewdirection(own_player["direction"], "left"))
            newx = newpos[1]
            newy = newpos[0]
            if ([state["height"] - 1, state["width"] - 1] >= newpos) & (newx >= 0) & (
                    newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                    if own_player["speed"] > 1:
                        hilfe = 0
                        for i in range(1, own_player["speed"]):
                            if counter % 6 == 0:         # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                                i = 1
                            newpos = getnewpos(own_player["x"], own_player["y"], i,
                                               getnewdirection(own_player["direction"], "left"))
                            newx = newpos[1]
                            newy = newpos[0]
                            if not state["cells"][newy][newx] == 0:
                                hilfe = 1
                        if hilfe == 0:
                            valid_actions += ["turn_left"]
                    else:
                        valid_actions += ["turn_left"]

            # check-right
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"],
                               getnewdirection(own_player["direction"], "right"))
            newx = newpos[1]
            newy = newpos[0]
            if ([state["height"] - 1, state["width"] - 1] >= newpos) & (newx >= 0) & (
                    newy >= 0):  # Prüfe ob er das Spielfeld verlassen würde
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                    if own_player["speed"] > 1:
                        hilfe = 0
                        for i in range(1, own_player["speed"]):
                            if counter % 6 == 0:         # Prüfe ob sechste runde und dann prüfe nicht Lücke (verschwenderisch)
                                i = 1
                            newpos = getnewpos(own_player["x"], own_player["y"], i,
                                               getnewdirection(own_player["direction"], "right"))
                            newx = newpos[1]
                            newy = newpos[0]
                            if not state["cells"][newy][newx] == 0:
                                hilfe = 1
                        if hilfe == 0:
                            valid_actions += ["turn_right"]
                    else:
                        valid_actions += ["turn_right"]

            action = random.choice(valid_actions)
            print(">", action)
            action_json = json.dumps({"action": action})
            await websocket.send(action_json)


asyncio.get_event_loop().run_until_complete(play())



