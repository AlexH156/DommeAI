import random


# Gets the current direction its headed and the change (left or right). Returns the new direction
def getNewDirection(direction, change):
    """Calculates a new direction based on your previous direction and the change

    :param direction: initial direction
    :param change: left or right
    :return: new direction
    """
    if direction == change: # (left + left | right + right) == down
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


# Returns a Boolean-Value if the snake jumped over another one
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
            # print("Über Schlange" + str(newy) + " " + str(newx))
            return True
    return False


# Return an answer according to the result(win or lose)
def trashTalk(own):
    """ Lines to print when a Game is won or not

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