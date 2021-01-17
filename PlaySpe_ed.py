#!/usr/bin/env python3
# TODO Handbuch
# TODO Dokumentation finalisieren
# TODO Reflektion/Ausblick
# TODO Softwarearchitektur und -qualität
# TODO Theoretische Ausarbeitung
# TODO Rechtschreibung, Grammatik etc
# TODO Screenshots in den Anhang

import time
import json
import websockets
import asyncio
from os import mkdir
from Agent import Agent
from AgentUtils import trashTalk, getGamePing
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
        if show:
            gameName = state["deadline"].replace(":","-")
            mkdir(gameName)

        while True:
            # print("<", state)
            if show:
                start = time.time()

            own = state["players"][str(state["you"])]
            if not state["running"] or not own["active"]:
                if badManner:
                    trashTalk(own)
                break

            indexAction, choices, de, isDeadend, checks, queueDepth, roundNumber, safeZone, deadline = spe_edAgent.gameStep(state)

            action = choices_actions[indexAction]
            print(">", action)

            action_json = json.dumps({"action": action})
            await websocket.send(action_json)

            if show:
                seconds = deadline - start
                createGUI(state, roundNumber, action, choices, queueDepth - 1, de, isDeadend, safeZone, seconds, gameName)

            state_json = await websocket.recv()
            state = json.loads(state_json)

asyncio.get_event_loop().run_until_complete(play(show=True, badManner=True))
