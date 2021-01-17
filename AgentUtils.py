import random
import dateutil.parser as dp
import requests
import time


def getNewDirection(direction, change):
    """Calculates a new direction based on your previous direction and the change

    :param direction: initial direction
    :param change: left or right
    :return: new direction
    """
    if direction == change:  # (left + left | right + right) == down
        return "down"
    if change == "left":    # turn left from direction
        if direction == "up":
            return "left"
        elif direction == "down":
            return "right"
        else:
            return "up"
    else:   # turn right from direction
        if direction == "down":
            return "left"
        elif direction == "up":
            return "right"
        else:
            return "up"


def getNewPos(x, y, speed, direction):
    """ Takes the current x and y-position, as well as speed and direction
        to determine the new head-position of the next step

    :param x: initial x Coordinate
    :param y: initial y Coordinate
    :param speed: speed to go in one Step
    :param direction: current direction to go
    :return: new position
    """
    if direction == "up":
        return y - speed, x
    elif direction == "down":
        return y + speed, x
    elif direction == "left":
        return y, x - speed
    else:
        return y, x + speed


def overSnake(x, y, board, direction, speed):
    """ Checks whether the player is jumping over a bot or a taken field

    :param x: x of the initial position from which he jumps from
    :param y: y of the initial position from which he jumps from
    :param board: board on which he performs the jump
    :param direction: direction the player is heading
    :param speed: speed of the player to calculate the jump length
    :return: boolean whether he is jumping over taken field or not
    """
    if speed < 3:
        return False
    for i in range(2, speed):
        newy, newx = getNewPos(x, y, i, direction)
        if board[newy][newx] != 0:
            return True
    return False


def getMinimalEnemyDistance(state, x, y):
    """
    :param state: the state of this round
    :param x: coordinate x
    :param y: coordinate y
    :return: Return the minimal manhattan-distance to the active enemies
    """
    dis = []

    for enemy in range(1, len(state["players"]) + 1):
        enemyObject = state["players"][str(enemy)]
        if enemyObject["active"] and not state["you"] == enemy:
            py = enemyObject["y"]
            px = enemyObject["x"]

            disXY = abs(px-x)+abs(py-y)
            dis.append(disXY)

    if not dis:
        return 0
    return min(dis)


def discardImpasse(px, py, dis, direction):
    """
    used in the calculations of checkDeadend() and maxLR()
    receives the current coordinates, on which the calculations were being based on and returns new coordinates,
    if the previous coordinates did not fulfill the requirements (free space to the left/right), as well as
    the new distance (distance-1)
    returns the coordinates, which are one step closer to the player

    :param px: x coordinate the calculations were beinf based on
    :param py: y coordinate the calculations were beinf based on
    :param dis: previous calculated distance
    :param direction: direction the calculations are being based on
    :return: new coordinates and (distance - 1)
    """
    if direction == "up":
        if dis > 0:
            py += 1
            dis -= 1
    elif direction == "down":
        if dis > 0:
            py -= 1
            dis -= 1
    elif direction == "right":
        if dis > 0:
            px -= 1
            dis -= 1
    else:  # left
        if dis > 0:
            px += 1
            dis -= 1
    return px, py, dis


def trashTalk(own):
    """
    Lines to print when a game is won or not

    :param own: own Player
    """
    if not own["active"]:
        answer = "GG WP"
    else:
        valid_responses = ["Winner Winner, Chicken Dinner", "git gud", "Too weak, too slow", "ez game, ez life",
                           "ez pz lemon squeezy", "ez", "rekt", "l2p", "noobs", "too ez", "nice tutorial",
                           "Are these bots on easy?", "This was so easy, I feel bad winning"]
        answer = random.choice(valid_responses)
    print(answer)


def getStepVector(direction):
    """
    :param direction: current direction of the snake
    :return: Return the y and x change, when one step in the given direction is taken
    """
    if direction == "up":
        return -1, 0
    elif direction == "down":
        return 1, 0
    elif direction == "right":
        return 0, 1
    else:
        return 0, -1
