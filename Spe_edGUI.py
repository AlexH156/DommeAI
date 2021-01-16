from matplotlib import pyplot, colors


def createGUI(state, counter, action, choices, depth, de, sackG, safeZone, timeToDeadline):
    """
    TODO
    :param safeZone:
    :param timeToDeadline:
    :param state:
    :param counter:
    :param action:
    :param choices:
    :param depth:
    :param de:
    :param sackG:
    """
    # information about the current state of the player
    youx = str(state["players"][str(state["you"])]["x"])
    youy = str(state["players"][str(state["you"])]["y"])
    youdir = str(state["players"][str(state["you"])]["direction"])
    youspeed = str(state["players"][str(state["you"])]["speed"])

    # values of the initial choices
    for i in range(0, 5):
        choices[i] = round(choices[i], 2)

    board = state["cells"]  # board as a 2D matrix
    w = max(state["width"] / 10, 5.8)  # width of the GUI (minimum value for the text)
    h = max(state["height"] / 10, 6)  # height of the GUI (addition for the text)

    # number of players
    playerCount = int(len(state["players"]))
    gameColors = ["grey", "white", "green", "blue", "orange", "red", "cyan", "magenta"]

    # replace the heads of the players with "-1" for the visualization
    # TODO: evtl nur aktive Spieler / oder zwischen aktiven und toten Köpfen unterscheiden
    for p in range(1, (playerCount + 1)):
        try:
            board[state["players"][str(p)]["y"]][state["players"][str(p)]["x"]] = -1
        except IndexError:  # if player died out of bounds
            pass

    # visualization using pyplot to create png files
    with pyplot.xkcd():  # style of the xkcd comics
        pyplot.figure(figsize=(w, h))

        # colors
        playerColors = gameColors[:(playerCount + 2)]
        colormap = colors.ListedColormap(playerColors)
        pyplot.imshow(board, cmap=colormap)  # vizualization of the board
        pyplot.title("DommeAI: " + gameColors[(state["you"] + 1)] + "\n" + "Seconds: " + str(round(timeToDeadline, 2)) +
                     " | Round: " + str(counter - 1))  # header

        # don't label the axis
        pyplot.xticks([])
        pyplot.yticks([])

        pyplot.xlabel("x: " + youx + " y: " + youy + " | dir: " + youdir + " | speed: " + youspeed +
                      " | De: " + str(de) + " | SZ: " + str(safeZone) +
                      "\n" + str(choices) + " | DE: " + str(sackG) +
                      "\n" + "next move: " + str(action) + "  |  depth: " + str(depth) +
                      " | Jump in T - " + str(5 - ((counter - 2) % 6)))

        pyplot.show(block=False)  # vizualization doesn't block the computations
