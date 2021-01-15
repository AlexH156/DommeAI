import time
from queue import Queue

import numpy as np
import dateutil.parser as dp
from AgentUtils import *


class Agent:
    """
    Agent is a class that calculates every possible and valid action from the current position.
    For every valid Action it calculates the next valid actions and iterates this process.

    Class Variables:
    width: width of the board
    height: height of the board
    roundNumber: number of the Game Round to calculate Jumps
    logActionValue: 2D Array, Arrays save evaluation on how many valid actions are possible from that action
                    in the specific layer
    jobQueue: Queue for every next Step that has to be checked whether it is valid or not
    countCDCalls: counts the number of executed jobs
    gamma: factor to discount valid actions based on their depth
    value: base value for every valid action
    deadline: later UTC time, server deadline until he needs the action answer
    board: game board

    """
    def __init__(self, board,width, height):
        self.width = width
        self.height = height
        self.roundNumber = 0
        self.logActionValue = []
        self.jobQueue = Queue()
        self.countCDCalls = 0  # Debugging
        self.gamma = 0.5  # Discount factor for every new Layer
        self.value = 1
        self.deadline = 0
        self.board = board
        self.sackG = False
        self.counter = 0

    def calcAction(self):
        """
        Aggregates the logActionValue by adding every layer values for every of the five possible actions.
        :return: action: best action based on the calculated values
                 choices: list of values, one value for every action
        """
        choices = [0, 0, 0, 0, 0]

        # Actions, that reach the deepest depth will be preferred (+10000)
        print(self.logActionValue)
        for i in range(0, 5):
            if len(self.logActionValue) > 1:
                if self.logActionValue[-2][i] != 0:
                    self.logActionValue[0][i] += 10000
            else:
                choices = self.logActionValue[0]

        # Add up the 2-D-array logActionValue to a 1-D-array choices
        for i in range(0, len(self.logActionValue)-1):
            for j in range(0, 5):
                choices[j] += self.logActionValue[i][j]

        # Choose the best action
        print(choices)
        indexAction = choices.index(max(choices))

        return indexAction, choices

    def isInBound(self, x, y):
        """
        :param x: the given coordinate x
        :param y: the given coordinate y
        :return: return if the given x or y is out of the playable board
        """
        return self.height > y >= 0 and self.width > x >= 0

    def checkFront(self, x, y, direction, speed, depth, initialAction, coord, distance,
                   collCounter, checkCounter):
        """
        Check if the actions slow-down, change-nothing and speed-up are possible. If an action is possible,
        add the value for the current depth to logActionValue and add all 5 sub-actions to the Queue
        :param x: the coordinate x of the snakes' head
        :param y: the coordinate y of the snakes' head
        :param direction: the direction the snake is headed
        :param speed: with what speed the snake is going (0<speed<11)
        :param depth: #TODO
        :param initialAction: either a given action (0 to 4) or None. Then initialise is for every case (SD, CN ,SU)
        :param coord: a list of coordinates, where the snake already was. Used to prevent hitting itself
        :param distance: the number of free fields in the current direction
        :param collCounter: number of consecutive turns in a specific direction
        :param checkCounter: number of turns in general
        :return: returns if move is not possible and therefore CN/SU are not possible as well
        """
        newAction = initialAction
        init = initialAction is None  # True, if this is the first call of checkFront
        coordIgnore = checkCounter < 3  # True, if coords doesn't have to be checked
        isJumping = self.counter % 6 == 0
        newCoord = coord[:]

        # Procedure: if there is a jump coming up, first check the common tail, then the specific head of the snake
        if isJumping:
            # common tail
            newBodyY, newBodyX = getNewPos(x, y, 1, direction)
            if self.isInBound(newBodyX, newBodyY) and self.board[newBodyY][newBodyX] == 0 \
                    and (coordIgnore or [newBodyY, newBodyX] not in coord):
                newCoord.append([newBodyY, newBodyX])

                # Slow-Down
                newHeadY, newHeadX = getNewPos(x, y, speed - 1, direction)
                if speed == 2 or (speed > 1 and self.isInBound(newHeadX, newHeadY) and self.board[newHeadY][newHeadX] == 0 and (coordIgnore or [newHeadY, newHeadX] not in coord)):
                    newCoord0 = newCoord[:]
                    if speed > 2:
                        newCoord0.append([newHeadY, newHeadX])
                    if init:
                        newAction = 1
                    self.logActionValue[depth][newAction] += self.value
                    if self.sackG and self.logActionValue[0][newAction] == 1 and overSnake(x, y, self.board, direction, speed - 1) and not self.checkDeadend(newHeadX, newHeadY, direction) < 14:
                        self.logActionValue[0][newAction] = 500
                    self.jobQueue.put((self.checkchoices, [newHeadX, newHeadY, direction, speed - 1, depth + 1,
                                                           newAction, newCoord0, distance, 0, checkCounter]))

                # Change-Nothing
                newHeadY, newHeadX = getNewPos(x, y, speed, direction)
                if self.isInBound(newHeadX, newHeadY) and self.board[newHeadY][newHeadX] == 0 \
                        and (coordIgnore or [newHeadY, newHeadX] not in coord):
                    newCoord1 = newCoord[:]
                    if speed > 1:
                        newCoord1.append([newHeadY, newHeadX])
                    if init:
                        newAction = 2
                    self.logActionValue[depth][newAction] += self.value
                    if self.sackG and self.logActionValue[0][newAction] == 1 \
                            and overSnake(x, y, self.board, direction, speed) and not self.checkDeadend(
                            newHeadX, newHeadY, direction) < 14:
                        self.logActionValue[0][newAction] = 500
                    self.jobQueue.put((self.checkchoices, [newHeadX, newHeadY, direction, speed,depth + 1, newAction,
                                                           newCoord1, distance, 0, checkCounter]))

                # Speed-Up
                newHeadY, newHeadX = getNewPos(x, y, speed + 1, direction)
                if speed < 10 and self.isInBound(newHeadX, newHeadY) and self.board[newHeadY][newHeadX] == 0 and (
                        coordIgnore or [newHeadY, newHeadX] not in coord):
                    newCoord2 = newCoord[:]
                    newCoord2.append([newHeadY, newHeadX])
                    if init:
                        newAction = 0
                    self.logActionValue[depth][newAction] += self.value
                    if self.sackG and self.logActionValue[0][newAction] == 1 and overSnake(x, y, self.board, direction,
                                                                                      speed + 1) and not self.checkDeadend(
                            newHeadX, newHeadY, direction) < 14:
                        self.logActionValue[0][newAction] = 500
                    self.jobQueue.put((self.checkchoices, [newHeadX, newHeadY, direction, speed + 1, depth + 1,
                                                           newAction, newCoord2, distance, 0, checkCounter]))

        # Procedure: If there is no Jump, check SD completely, then the head of CN, then the head of SU
        else:
            newCoord0 = coord[:]
            # Slow-Down
            if speed > 1:
                newHeadY, newHeadX = getNewPos(x, y, speed - 1, direction)
                if self.isInBound(newHeadX, newHeadY) and self.board[newHeadY][newHeadX] == 0 and (
                        coordIgnore or [newHeadY, newHeadX] not in coord):
                    newCoord0.append([newHeadY, newHeadX])
                    for i in range(1, speed - 1):
                        newBodyY, newBodyX = getNewPos(x, y, i, direction)
                        if self.board[newBodyY][newBodyX] != 0 or (not coordIgnore and [newBodyY, newBodyX] in coord):
                            return
                        newCoord0.append([newBodyY, newBodyX])
                    if init:
                        newAction = 1
                    self.logActionValue[depth][newAction] += self.value
                    self.jobQueue.put((self.checkchoices, [newHeadX, newHeadY, direction, speed - 1, depth + 1,
                                                           newAction, newCoord0, distance, 0, checkCounter]))
                else:
                    return

            # Change-Nothing
            newHeadY, newHeadX = getNewPos(x, y, speed, direction)
            if self.isInBound(newHeadX, newHeadY) and self.board[newHeadY][newHeadX] == 0 and \
                    (coordIgnore or [newHeadY, newHeadX] not in coord):
                newCoord1 = newCoord0[:]
                newCoord1.append([newHeadY, newHeadX])
                if init:
                    newAction = 2
                self.logActionValue[depth][newAction] += self.value
                self.jobQueue.put((self.checkchoices, [newHeadX, newHeadY, direction, speed, depth + 1, newAction,
                                                       newCoord1, distance, 0, checkCounter]))

                # Speed-Up
                newHeadY, newHeadX = getNewPos(x, y, speed + 1, direction)
                if speed < 10 and self.isInBound(newHeadX, newHeadY) and self.board[newHeadY][newHeadX] == 0 \
                        and (coordIgnore or [newHeadY, newHeadX] not in coord):
                    newCoord2 = newCoord1[:]
                    newCoord2.append([newHeadY, newHeadX])
                    if init:
                        newAction = 0
                    self.logActionValue[depth][newAction] += self.value
                    self.jobQueue.put((self.checkchoices, [newHeadX, newHeadY, direction, speed + 1,depth + 1,
                                                           newAction, newCoord2, distance, 0, checkCounter]))

    def checkLeftorRight(self, x, y, direction, speed, depth, action, coord, collCounter,
                         checkCounter, change, distance):
        """
        Check if the action left/right is possible. If it is possible,
        add the value for the current depth to logActionValue and add all 5 sub-actions to the Queue
        :param x: the coordinate x of the snakes' head
        :param y: the coordinate y of the snakes' head
        :param direction: the direction the snake is headed
        :param speed: with what speed the snake is going (0<speed<11)
        :param depth: TODO
        :param action: the action on which this move is first based
        :param coord: a list of coordinates, where the snake already was. Used to prevent hitting itself
        :param distance: the number of free fields in the current direction
        :param collCounter: number of consecutive turns in a specific direction
        :param checkCounter: number of turns in general
        :param change: Either "left" or "right". Determines which direction should be checked
        :return: returns if move is not possible and therefore CN/SU are not possible as well
        """
        coordIgnore = checkCounter < 2  # True, if coords doesn't have to be checked, because he didn't turn twice
        direction = getNewDirection(direction, change)
        isJumping = self.counter % 6 == 0
        newcoord = coord[:]

        newheadY, newheadX = getNewPos(x, y, speed, direction)
        if (change == "left" and collCounter != -2 or change == "right" and collCounter != 2) and self.isInBound(
                newheadX, newheadY) and self.board[newheadY][newheadX] == 0 and (
                coordIgnore or [newheadY, newheadX] not in coord):
            newcoord.append([newheadY, newheadX])
            for i in range(1, speed):
                if isJumping:  # If it is the sixth round, skip the occuring gap
                    newbodyY, newbodyX = getNewPos(x, y, 1, direction)
                    if self.board[newbodyY][newbodyX] != 0 or (not coordIgnore and [newbodyY, newbodyX] in coord):
                        return
                    newcoord.append([newbodyY, newbodyX])
                    break
                newbodyY, newbodyX = getNewPos(x, y, i, direction)
                if self.board[newbodyY][newbodyX] != 0 or (not coordIgnore and [newbodyY, newbodyX] in coord):
                    return
                newcoord.append([newbodyY, newbodyX])
            self.logActionValue[depth][action] += self.value
            if isJumping and self.logActionValue[0][action] == 1 and self.sackG \
                    and overSnake(x, y, self.board, direction, speed) and not self.checkDeadend(
                    newheadX, newheadY, direction) < 14:
                self.logActionValue[0][action] = 500
            if change == "left":
                if collCounter <= 0:
                    checkCounter += 1
                collCounter = min(collCounter - 1, - 1)
            else:
                if collCounter >= 0:
                    checkCounter += 1
                collCounter = max(collCounter + 1, 1)

            # TODO Prüfen, ob effizienter
            # if distance == 0 and myc < 6 and coordIgnore:
            #     distance = self.getDistance(newheadX, newheadY, self.board, direction, self.width, self.height) + speed

            self.jobQueue.put((self.checkdistance, [newheadX, newheadY, direction, speed, depth + 1,
                                      action, newcoord, distance - speed, collCounter,checkCounter]))

    def constructEnemyBoard(self, state, isJumping):
        """Calculates the Board with every possible step of the enemies, to dodge an overlap in the next
        action and to take the enemy steps into account for estimating the best action

        :param state: the current state
        :param isJumping: is the snake jumping in this round
        :return: Return a board that has every possible action from active enemies registered
        """
        enemyBoard = [row[:] for row in state["cells"]]
        # check every active player
        for enemy in range(1, len(state["players"]) + 1):
            enemyObject = state["players"][str(enemy)]
            if enemyObject["active"] and not state["you"] == enemy:
                # first check, whether it would survive a speed_down, register it
                # then check change_nothing and register it
                # finally check speed_up and register that
                # (special case if it is a jump round)
                newHeadPosList = []
                currDirection = enemyObject["direction"]
                speedNotTen = 1
                if enemyObject["speed"] % 10 == 0:
                    newSpeed = 10
                    speedNotTen = 0
                else:
                    newSpeed = enemyObject["speed"] + 1

                newHeadPosList.append(getNewPos(enemyObject["x"], enemyObject["y"], newSpeed, currDirection))

                newDirection = getNewDirection(currDirection, "left")
                newHeadPosList.append(getNewPos(enemyObject["x"], enemyObject["y"], enemyObject["speed"], newDirection))

                newDirection = getNewDirection(currDirection, "right")
                newHeadPosList.append(getNewPos(enemyObject["x"], enemyObject["y"], enemyObject["speed"], newDirection))

                if isJumping:
                    pathList = [np.zeros(newSpeed, dtype=np.int32)]
                    pathList[0][0] = 7
                    pathList[0][-1] = 7
                    pathList[0][-2] = 7

                    pathList.append(np.zeros(newSpeed - 1 * speedNotTen, dtype=np.int32))
                    pathList[1][0] = 7
                    pathList[1][-1] = 7

                    if newSpeed >= 3:
                        pathList[0][-3] = 7
                else:
                    pathList = [np.full(newSpeed, 7, dtype=np.int32),
                                np.full((newSpeed - 1 * speedNotTen), 7, dtype=np.int32)]

                pathNum = 0
                for newHeadPos in newHeadPosList:
                    stepVector = [newHeadPos[0] - enemyObject["y"], newHeadPos[1] - enemyObject["x"]]

                    if stepVector[1] == 0:
                        stepVector[0] = stepVector[0] / abs(stepVector[0])
                        boundHelp = (stepVector[0] + 1) * 0.5
                        numberSteps = min(abs(boundHelp * (self.height - 1) - enemyObject["y"]),
                                          newSpeed - 1 * pathNum * speedNotTen)
                    else:
                        stepVector[1] = stepVector[1] / abs(stepVector[1])
                        boundHelp = (stepVector[1] + 1) * 0.5
                        numberSteps = min(abs(boundHelp * (self.width - 1) - enemyObject["x"]),
                                          newSpeed - 1 * pathNum * speedNotTen)

                    chosenPath = pathList[pathNum]
                    numberSteps = int(numberSteps)
                    for step in range(1, numberSteps + 1):
                        stepX = enemyObject["x"] + stepVector[1] * step
                        stepY = enemyObject["y"] + stepVector[0] * step
                        enemyBoard[int(stepY)][int(stepX)] = max(chosenPath[step - 1],
                                                                 enemyBoard[int(stepY)][int(stepX)])
                    pathNum = 1
        return enemyBoard

    def getDistance(self, x, y, direction):
        """Gives the distance of free fields in a given directory from a given point

        :param x: coordinate x
        :param y: coordinate y
        :param direction: the given direction
        :return: Return the count of free fields in the given direction
        """
        dis = 0
        if direction == "up":
            while y > 0 and self.board[y - 1][x] == 0:
                y -= 1
                dis += 1
        elif direction == "down":
            while y < self.height - 1 and self.board[y + 1][x] == 0:
                y += 1
                dis += 1
        elif direction == "right":
            while x < self.width - 1 and self.board[y][x + 1] == 0:
                x += 1
                dis += 1
        else:  # left
            while x > 0 and self.board[y][x - 1] == 0:
                x -= 1
                dis += 1
        return dis

    # TODO In diesem Szenario leicht anderes Ergebnis
    def checkdistance(self, x, y, direction, speed, depth, action, coord,
                      distance, collCounter, checkCounter):
        # self.checkD += 1  # Debugging

        if self.checkDeadline():
            return

        self.checkNewLayer(depth)

        # if distance > speed+1:
        # logActionValue += ..., etc
        # add to Queue: SU, CN, SD (CheckDistance)
        # board und cd werte jeweils aktualisieren

        # checkleft, checkright

        # ist es in diesem Schritt möglich? -> CC
        # elif distance == speed+1:
        # logActionValue += ..., etc
        # add to Queue: SU, CN, SD (CheckChoices)
        # board und cc werte jeweils aktualisieren

        # ist es in diesem Zug möglich
        if distance > speed:
            if distance == (speed + 1):
                checkWhat = self.checkchoices
            else:
                checkWhat = self.checkdistance

            newaction = action
            init = action is None
            isJumping = self.counter % 6 == 0

            newcoord = coord[:]

            # ist es evtl im nächsten Schritt möglich? -> CD
            if isJumping:
                newy, newx = getNewPos(x, y, 1, direction)
                newcoord.append([newy, newx])

                # speed_down in queue
                if speed > 1:
                    newy, newx = getNewPos(x, y, speed - 1, direction)
                    newcoord0 = newcoord[:]
                    if speed > 2:
                        newcoord0.append([newy, newx])
                    if init:
                        newaction = 1
                    self.logActionValue[depth][newaction] += self.value
                    self.jobQueue.put((checkWhat, [newx, newy, direction, speed - 1,
                                                   depth + 1, newaction, newcoord0,
                                                   distance - (speed - 1), 0, checkCounter]))

                # change_nothing
                newy, newx = getNewPos(x, y, speed, direction)
                newcoord1 = newcoord[:]
                newcoord1.append([newy, newx])
                if init:
                    newaction = 2
                self.logActionValue[depth][newaction] += self.value
                self.jobQueue.put((checkWhat, [newx, newy, direction, speed,
                                               depth + 1, newaction, newcoord1, distance - speed, 0, checkCounter]))
                # speed_up
                if speed < 10:
                    newy, newx = getNewPos(x, y, speed + 1, direction)
                    newcoord2 = newcoord[:]
                    newcoord2.append([newy, newx])
                    if init:
                        newaction = 0
                    self.logActionValue[depth][newaction] += self.value
                    self.jobQueue.put((checkWhat, [newx, newy, direction, speed + 1,
                                                   depth + 1, newaction, newcoord2,
                                                   distance - (speed + 1), 0, checkCounter]))
            else:
                if speed > 1:
                    for i in range(1, speed - 1):
                        newyy, newxx = getNewPos(x, y, i, direction)
                        newcoord.append([newyy, newxx])
                    # speed_down
                    newy, newx = getNewPos(x, y, speed - 1, direction)
                    if speed > 2:
                        newcoord.append([newy, newx])
                    if init:
                        newaction = 1
                    self.logActionValue[depth][newaction] += self.value
                    self.jobQueue.put((checkWhat, [newx, newy, direction, speed - 1,
                                                   depth + 1, newaction, newcoord,
                                                   distance - (speed - 1), 0, checkCounter]))
                # change_nothing
                newy, newx = getNewPos(x, y, speed, direction)
                newcoord1 = newcoord[:]
                newcoord1.append([newy, newx])
                if init:
                    newaction = 2
                self.logActionValue[depth][newaction] += self.value
                self.jobQueue.put((checkWhat, [newx, newy, direction, speed, depth + 1, newaction, newcoord1,
                                               distance - speed, 0, checkCounter]))

                # speed_up
                if speed < 10:
                    newy, newx = getNewPos(x, y, speed + 1, direction)
                    newcoord2 = newcoord1[:]
                    newcoord2.append([newy, newx])
                    if init:
                        newaction = 0
                    self.logActionValue[depth][newaction] += self.value
                    self.jobQueue.put((checkWhat, [newx, newy, direction, speed + 1,
                                                   depth + 1, newaction, newcoord2,
                                                   distance - (speed + 1), 0, checkCounter]))

            # init bedeutet ist erster Aufruf und daher wird LR extra aufgerufen
            if not init:
                # check-left
                self.checkLeftorRight(x, y, direction, speed, depth, action,
                                      coord, collCounter, checkCounter, "left", 0)

                # check-right
                self.checkLeftorRight(x, y, direction, speed, depth, action,
                                      coord, collCounter, checkCounter, "right", 0)

        # If the distance is not bigger than the speed, call checkchoices to check for possible jumps
        else:
            self.checkchoices(x, y, direction, speed, depth, action, coord, 0, collCounter, checkCounter)

    def checkchoices(self, x, y, direction, speed, depth, action, coord, distance,
                     collCounter, checkCounter):
        """
        First, check if less than a second to the deadline is left. If so, drop the Queue and return
        If not, check if a new layer has been reached. Then call functions to check the 5 actions
        :param x: the coordinate x of the snakes' head
        :param y: the coordinate y of the snakes' head
        :param direction: the direction the snake is headed
        :param speed: with what speed the snake is going (0<speed<11)
        :param depth: TODO
        :param action: the action on which this move is first based
        :param coord: a list of coordinates, where the snake already was. Used to prevent hitting itself
        :param distance: the number of free fields in the current direction
        :param collCounter: number of consecutive turns in a specific direction
        :param checkCounter: number of turns in general
        :return: returns if less than a second to the deadline is left
        """

        if self.checkDeadline():
            return

        self.checkNewLayer(depth)

        # Check-SD/CN/SU
        self.checkFront(x, y, direction, speed, depth, action, coord, 0, collCounter, checkCounter)

        # Check-Left
        self.checkLeftorRight(x, y, direction, speed, depth, action, coord, collCounter, checkCounter, "left", 0)

        # Check-Right
        self.checkLeftorRight(x, y, direction, speed, depth, action, coord, collCounter, checkCounter, "right", 0)

    # TODO evtl durch 2 aufrufe von getDistance ersetzen
    # computes the maximum distance to the left and right of a direction and coordinates
    def maxLR(self, x, y, direction):
        px = x
        py = y

        # computes the direction to the rigth
        ld = 0
        if direction == "right":  # checks up  (left of right)
            while py > 0 and self.board[py - 1][px] == 0:
                py -= 1
                ld += 1
        elif direction == "left":  # checks down
            while py < self.height - 1 and self.board[py + 1][px] == 0:
                py += 1
                ld += 1
        elif direction == "down":  # checks right
            while px < self.width - 1 and self.board[py][px + 1] == 0:
                px += 1
                ld += 1
        else:  # checks left
            while px > 0 and self.board[py][px - 1] == 0:
                px -= 1
                ld += 1

        px = x
        py = y

        # computes the direction to the left
        rd = 0
        if direction == "left":  # checks up (right of left)
            while py > 0 and self.board[py - 1][px] == 0:
                py -= 1
                rd += 1
        elif direction == "right":  # checks down
            while py < self.height - 1 and self.board[py + 1][px] == 0:
                py += 1
                rd += 1
        elif direction == "up":  # checks right
            while px < self.width - 1 and self.board[py][px + 1] == 0:
                px += 1
                rd += 1
        else:  # checks left
            while px > 0 and self.board[py][px - 1] == 0:
                px -= 1
                rd += 1

        return max(ld, rd)

    # computes the maximum possible number of fields in one direction including one turn at the end
    def deadendDir(self, x, y, direction):
        px = x
        py = y

        dis = 0
        if direction == "up":
            while py > 0 and self.board[py - 1][px] == 0:
                py -= 1
                dis += 1
        elif direction == "down":
            while py < self.height - 1 and self.board[py + 1][px] == 0:
                py += 1
                dis += 1
        elif direction == "right":
            while px < self.width - 1 and self.board[py][px + 1] == 0:
                px += 1
                dis += 1
        else:  # left
            while px > 0 and self.board[py][px - 1] == 0:
                px -= 1
                dis += 1

        LR = self.maxLR(px, py, direction)

        while LR == 0:  # if maxLR == 0: check one step back
            if direction == "up":   # TODO testen
                if py < y:
                    py += 1
                    dis -= 1
                else:
                    break
            elif direction == "down":
                if py > y:
                    py -= 1
                    dis -= 1
                else:
                    break
            elif direction == "right":
                if px > x:
                    px -= 1
                    dis -= 1
                else:
                    break
            else:  # left
                if px < x:
                    px += 1
                    dis -= 1
                else:
                    break
            LR = self.maxLR(px, py, direction)

        return dis + LR

    # computes a value describing whether the given coordinates are inside a deadend
    # the lower the value, the closer the space (value < 14 = deadend)
    def checkDeadend(self, x, y, direction):
        straight = self.deadendDir(x, y, direction)
        right = self.deadendDir(x, y, getNewDirection(direction, "right"))
        left = self.deadendDir(x, y, getNewDirection(direction, "left"))
        return max(straight, right, left)

    def checkNewLayer(self, depth):
        """
        If logActionValue is not longer than the depth, append it, and update some variables for the new layer
        :param depth: #TODO
        """
        if not len(self.logActionValue) > depth:
            self.logActionValue.append([0, 0, 0, 0, 0])
            self.value = self.value * self.gamma
            self.counter = self.roundNumber + depth  # TODO prüfen, ob passt

    def checkDeadline(self):
        """
        :return: Drop the Queue and return, if less than a second remains to the deadline
                and he checked more than 4 layers
        """
        if time.time() + 1 > self.deadline:
            if len(self.logActionValue) > 4:
                with self.jobQueue.mutex:
                    self.jobQueue.queue.clear()
                return True
        return False

    def gameStep(self, state):
        # Initialization
        depth = 0
        self.roundNumber += 1
        self.counter = self.roundNumber
        self.value = 1
        isJumping = self.roundNumber % 6 == 0
        self.logActionValue = [[0, 0, 0, 0, 0]]
        self.deadline = dp.parse(state["deadline"]).timestamp()
        checks, checkD = 0, 0  # Debugging

        # create a board, which includes every next move of the active enemies
        # also includes moves leading to a potential death of an enemy
        self.board = self.constructEnemyBoard(state, isJumping)

        # Debugging:
        # LR = maxLR(own["x"], own["y"], board, own["direction"])
        # deDir = deadendDir(own["x"], own["y"], board, own["direction"])
        own = state["players"][str(state["you"])]
        de = self.checkDeadend(own["x"], own["y"], own["direction"])
        self.sackG = de < 14    # TODO testen if Wert > 40 and Round > 300 and Distanz zu Gegnern > x: SD + 100, SU - 100

        # Catches the special case, when the possible moves of an enemy blocks our snake. We will then proceed
        # with the basic board, that doesn´t have the enemies' possible moves included
        while True:
            # check the unoccupied distance in all directions

            straightDistance = self.getDistance(own["x"], own["y"], own["direction"])
            leftDistance = self.getDistance(own["x"], own["y"], getNewDirection(own["direction"], "left"))
            rightDistance = self.getDistance(own["x"], own["y"], getNewDirection(own["direction"], "right"))

            if straightDistance > own["speed"]:
                checkWhat = self.checkdistance
            else:
                checkWhat = self.checkFront

            checkWhat(own["x"], own["y"], own["direction"], own["speed"], depth,
                      None, [], straightDistance, 0, 0)

            # check-left
            self.checkLeftorRight(own["x"], own["y"], own["direction"], own["speed"], depth,
                                  3, [], 0, 0, "left", leftDistance)

            # check-right
            self.checkLeftorRight(own["x"], own["y"], own["direction"], own["speed"], depth,
                                  4, [], 0, 0, "right", rightDistance)

            # works on objects in the queue until it is either empty or the deadline is just one second away
            while not self.jobQueue.empty():
                checks += 1  # Debugging
                f, args = self.jobQueue.get()
                f(*args)

            if len(self.logActionValue) > 0:
                break

            # if there are no possible move, when the first moves of the enemies are accounted for, they are discarded
            self.board = state["cells"]

        indexAction, choices = self.calcAction()
        return indexAction, choices, de, self.sackG, checks, self.queueDepth, self.roundNumber, checkD
