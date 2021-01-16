#!/usr/bin/env python3
# TODO imports prüfen
# TODO Handbuch
import time
from datetime import datetime
import json
import dateutil.parser as dp
import requests
import websockets
from Agent import Agent
from AgentUtils import trashTalk
import asyncio
from Spe_edGUI import createGUI


async def play(show=False, badManner=True):
    """ Function to connect with the websocket, create the Agent and
    calculate the estimated best action and sends it back to the websocket

    :param show: Boolean, whether the Game should be displayed in a GUI
    :param badManner: Boolean, whether a 'toxic' message upon winning should be printed
    """

    url = "wss://msoll.de/spe_ed"
    key = open('apikey.txt', "r").read().strip()
    async with websockets.connect(f"{url}?key={key}") as websocket:
        print("Waiting for initial state...", flush=True)
        choices_actions = ["speed_up", "slow_down", "change_nothing", "turn_left", "turn_right"]

        state_json = await websocket.recv()
        state = json.loads(state_json)

        spe_edAgent = Agent(state["width"], state["height"])
        while True:
            start = time.time()
            timeAPI = requests.get("https://msoll.de/spe_ed_time")
            serverTime = dp.parse(timeAPI.json()["time"]).timestamp() + timeAPI.json()["milliseconds"]/1000
            ping = serverTime-start
            print("Ping", ping)
            print("<", state)
            print("Startzeit: " + str(datetime.utcnow()))  # Debugging

            own = state["players"][str(state["you"])]
            if not state["running"] or not own["active"]:
                if badManner:
                    trashTalk(own)
                break

            indexAction, choices, de, isDeadend, checks, queueDepth, roundNumber, checkD, safeZone, deadline = spe_edAgent.gameStep(state)

            print("Endzeit: " + str(datetime.utcnow()))  # Debugging
            print("\n", checks, "davon checkD:", checkD)  # Debugging
            action = choices_actions[indexAction]
            print(">", action)

            seconds = deadline - start

            action_json = json.dumps({"action": action})
            await websocket.send(action_json)

            if show:
                createGUI(state, roundNumber, action, choices, queueDepth - 1, de, isDeadend, safeZone, seconds)

            state_json = await websocket.recv()
            state = json.loads(state_json)

asyncio.get_event_loop().run_until_complete(play(show=True, badManner=True))
