from datetime import datetime
import json
import websockets
from Agent import Agent
from AgentUtils import trashTalk
import asyncio
from Spe_edGUI import createGUI


async def play(show=False, badManner=True):
    """ Function to connect with websocket, create the Agent and
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
        spe_edAgent = Agent(state["cells"], state["width"], state["height"])
        while True:
            print("<", state)
            print("Startzeit: " + str(datetime.utcnow()))

            own = state["players"][str(state["you"])]
            if not state["running"] or not own["active"]:
                if badManner:
                    trashTalk(own)
                # pyplot.show()
                break

            indexAction, choices, de, sackG, checks, queueDepth, roundNumber, checkD = spe_edAgent.gameStep(state)

            print("Endzeit: " + str(datetime.utcnow()))
            print("\n", checks, "davon checkD:", checkD)
            action = choices_actions[indexAction]
            print(">", action)

            action_json = json.dumps({"action": action})
            await websocket.send(action_json)

            if show:  # GUI, falls show == True
                createGUI(state, roundNumber, action, choices, queueDepth - 1, de, sackG)

            state_json = await websocket.recv()
            state = json.loads(state_json)

asyncio.get_event_loop().run_until_complete(play(show=True, badManner=True))
