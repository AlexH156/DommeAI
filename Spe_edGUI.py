from matplotlib import pyplot, colors


def createGUI(state, counter, action, choices, depth, de, isDeadend, isSafeZone, timeToDeadline, gameName):
    """
    Saves a *.jpg of the board with additional meta-data per Round in the previously created folder gameName

    :param state: state, used to get the board as well as player-information
    :param counter: the round-number
    :param action: what action the snake did on this state
    :param choices: the values of each action
    :param depth: the depth the snake reached with its calculations
    :param de: the "deadend-value"
    :param isDeadend: bool, if its in a dead end
    :param isSafeZone: bool, if the enemies are far away and it has enough space around itself
    :param timeToDeadline: the time for this round
    :param gameName: the name of the game where the pictures should be saved
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

        pyplot.savefig(str(gameName) + "/" + str(counter - 1) + ".jpg", format="jpg")
        pyplot.close()
        # pyplot.show(block=False)  # if not commentated it shows the GUI directly (tested in PyCharm Professional)
