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
        return [x, y - s]
    elif dir == "down":
        return [x, y + s]
    elif dir == "left":
        return [x - s, y]
    elif dir == "right":
        return [x + s, y]

async def play():
    url = os.environ["URL"]
    key = os.environ["KEY"]

    async with websockets.connect(f"{url}?key={key}") as websocket:
        print("Waiting for initial state...", flush=True)
        while True:
            state_json = await websocket.recv()
            state = json.loads(state_json)
            print("<", state)
            own_player = state["players"][str(state["you"])]
            if not state["running"] or not own_player["active"]:
                break
            valid_actions = []

            #check-speedup
            if own_player["speed"] < 10:
                newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"]+1, own_player["direction"])
                if ([state["width"] - 1, state["height"] - 1] >= newpos) & (
                        newpos >= [0, 0]):  # Prüfe ob er das Spielfeld verlassen würde
                    newx = newpos[0]
                    newy = newpos[1]
                    if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an der neuen Stelle ist
                        valid_actions += ["speed_up"]

            #check-speeddown
            if own_player["speed"] > 1:
                newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"]-1, own_player["direction"])
                if ([state["width"] - 1, state["height"] - 1] >= newpos) & (
                        newpos >= [0, 0]):  # Prüfe ob er das Spielfeld verlassen würde
                    newx = newpos[0]
                    newy = newpos[1]
                    if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an der neuen Stelle ist
                        valid_actions += ["slow_down"]

            # check-nothing
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"], own_player["direction"])
            if ([state["width"] - 1, state["height"] - 1] >= newpos) & (newpos >= [0, 0]):  # Prüfe, ob er das Spielfeld verlassen würde
                newx = newpos[0]
                newy = newpos[1]
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an der neuen Stelle ist
                    valid_actions += ["change_nothing"]

            # check-left
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"],
                               getnewdirection(own_player["direction"], "left"))
            if ([state["width"] - 1, state["height"] - 1] >= newpos) & (newpos >= [0, 0]):  # Prüfe auf Spielrand verlassen wenn nach links
                newx = newpos[0]
                newy = newpos[1]
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an der neuen Stelle ist
                    valid_actions += ["turn_left"]

            # check-right
            newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"],
                               getnewdirection(own_player["direction"], "right"))
            if ([state["width"] - 1, state["height"] - 1] >= newpos) & (newpos >= [0, 0]):  # Prüfe auf Spielrand verlassen wenn nach rechts
                newx = newpos[0]
                newy = newpos[1]
                if state["cells"][newy][newx] == 0:  # Prüfe ob Schlange an der neuen Stelle ist
                    valid_actions += ["turn_right"]

            action = random.choice(valid_actions)
            print(">", action)
            action_json = json.dumps({"action": action})
            await websocket.send(action_json)


asyncio.get_event_loop().run_until_complete(play())



