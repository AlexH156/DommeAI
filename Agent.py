from queue import Queue
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

    def __init__(self, width, height, ping):
        """
        Initialise the following variables at the start of a game

        :param width: the width of the board
        :param height: the height of the board
        :param ping: difference between server time and runtime
        """
        self.width = width
        self.height = height
        self.ping = ping
        self.roundNumber = 0
        self.logActionValue = []
        self.jobQueue = Queue()
        self.countCDCalls = 0  # Debugging
        self.value = 1
        self.deadline = 0
        self.board = []
        self.isDeadend = False
        self.isSafeZone = False
        self.counter = 0

        # Configuration Values:
        self.timePuffer = 0.3
        self.gamma = 0.5  # Discount factor for every new Layer
        self.deadendBias = 500
        self.safeZoneBias = 0.5  # Bias pro speed_down and contra speed_up if in a safeZone
        self.deadendLimit = 14  # Limit, when a situation is considered a deadend
        self.safeZoneLimit = 35  # Limit, when a situation could be considered a safeZone
        self.safeZoneDistance = 20  # Limit, when a possible safeZone is called

    def calcAction(self):
        """
        Aggregates the logActionValue by adding every layer values for every of the five possible actions.

        :return: action: best action based on the calculated values
                 choices: list of values, one value for every action
        """
        choices = [0, 0, 0, 0, 0]

        print(self.logActionValue)  # Debugging

        if self.isSafeZone:
            self.logActionValue[0][1] *= (1 + self.safeZoneBias)  # prefer speed_down, if in a safeZone
            self.logActionValue[0][0] *= (1 - self.safeZoneBias)  # punish speed_up, if in a safeZone

        # Gather actions, that don't reach the deepest depth
        noDepth = []
        for i in range(0, len(choices)):
            if len(self.logActionValue) > 1:
                if self.logActionValue[-2][i] == 0:
                    noDepth.append(i)
            else:
                choices = self.logActionValue[0]

        # Add up the 2-D-array logActionValue to a 1-D-array choices
        for i in range(0, len(self.logActionValue) - 1):
            for j in range(0, len(choices)):
                choices[j] += self.logActionValue[i][j]

        # Actions, that don't reach the deepest depth will set to -1
        for i in noDepth:
            choices[i] = -1

        # Choose the best action
        indexAction = choices.index(max(choices))

        return indexAction, choices

    def isInBound(self, x, y):
        """
        :param x: the given coordinate x
        :param y: the given coordinate y
        :return: return if the given x or y is out of the playable board
        """
        return self.height > y >= 0 and self.width > x >= 0

    def isNotTaken(self, x, y, coordIgnore, coord):
        """
        Check, whether the position is already taken by an enemy snake or the own

        :param x: coordinate x
        :param y: coordinate y
        :param coordIgnore: If True, coords do not have to be checked
        :param coord: A list of coordinates, where the own snake was
        :return:
        """
        return self.board[y][x] == 0 and (coordIgnore or [y, x] not in coord)

    def isValid(self, x, y, coordIgnore, coord):
        """
        Combination of isInBound and isNotTaken for better visualisation
        """
        return self.isInBound(x, y) and self.isNotTaken(x, y, coordIgnore, coord)

    def isAbleToJumpInDeadend(self, newAction, x, y, direction, speed, newX, newY):
        """
        :param newAction: the action on that the jump is based
        :param x: the current x coordinate
        :param y: the current y coordinate
        :param direction: the current direction
        :param speed: the current speed
        :param newX: the new x coordinate after jump
        :param newY: the new y coordinate after jump
        :return: True, if the snake is in a dead end, has the ability to jump over a snake into a field,
                that has is no dead end. self.logActionValue[0][newAction] == 1 checks if he already calculated it
        """
        return self.isDeadend and self.logActionValue[0][newAction] == 1 and \
               overSnake(x, y, self.board, direction, speed) and not self.checkDeadend(newX, newY, direction, 1) < 14

    def checkFront(self, x, y, direction, speed, depth, initialAction, coord, distance, checkCounter):
        # TODO Kommentare @Wiggi
        """
        Check if the actions slow-down, change-nothing and speed-up are possible. If an action is possible,
        add the value for the current depth to logActionValue and add checkChoices to the jobQueue

        :param x: the coordinate x of the snakes' head
        :param y: the coordinate y of the snakes' head
        :param direction: the direction the snake is headed
        :param speed: with what speed the snake is going (0<speed<11)
        :param depth: the current depth of how deep the snake checked its moves
        :param initialAction: either a given action (0 to 4) or None. Then initialise is for every case (SD, CN ,SU)
        :param coord: a list of coordinates, where the snake already was. Used to prevent hitting itself
        :param distance: the number of free fields in the current direction
        :param checkCounter: number of turns in general
        :return: returns if move is not possible and therefore CN/SU are not possible as well
        """
        stepVectorY, stepVectorX = getStepVector(direction)

        coordIgnore = checkCounter < 3
        xValid = x + stepVectorX
        yValid = y + stepVectorY

        if not self.isValid(xValid, yValid, coordIgnore, coord):
            return

        isJumping = self.counter % 6 == 0
        move = [False, False, False]

        skip = distance > speed  # True, if other checks can be skipped due to distance

        newCoord = coord[:]
        newCoord.append([yValid, xValid])
        newCoord0, newCoord1, newCoord2 = [], [], []

        xSD, ySD = x + stepVectorX * (speed - 1), y + stepVectorY * (speed - 1)
        if skip or self.isInBound(xSD, ySD):
            if speed > 1 and (skip or self.isNotTaken(xSD, ySD, coordIgnore, coord)):
                move[0] = True
                if speed > 2:
                    newCoord0.append([ySD, xSD])

            xCN, yCN = xSD + stepVectorX, ySD + stepVectorY
            if speed == 1 or skip or self.isInBound(xCN, yCN):
                if speed == 1 or skip or self.isNotTaken(xCN, yCN, coordIgnore, coord):
                    move[1] = True
                    if speed > 1:
                        newCoord1.append([yCN, xCN])

                if speed < 10:
                    xSU, ySU = xCN + stepVectorX, yCN + stepVectorY
                    if skip or self.isValid(xSU, ySU, coordIgnore, coord):
                        move[2] = True
                        newCoord2.append([ySU, xSU])
        else:
            return

        if not isJumping:
            xAdd, yAdd = x + stepVectorX, y + stepVectorY

            for i in range(2, speed - 1):
                xAdd, yAdd = xAdd + stepVectorX, yAdd + stepVectorY
                if not skip and not self.isNotTaken(xAdd, yAdd, coordIgnore, coord):
                    return
                newCoord.append([yAdd, xAdd])

            move[1] = move[1] and (move[0] or speed == 1)
            move[2] = move[2] and move[1]

        init = initialAction is None
        for i in range(3):

            if init:
                initialAction = [1, 2, 0][i]

            if move[i]:
                newActionCoord = [newCoord0, newCoord1, newCoord2][i] + newCoord
                self.logActionValue[depth][initialAction] += self.value
                newSpeed = (speed + i - 1)
                newX, newY = x + stepVectorX * newSpeed, y + stepVectorY * newSpeed
                if self.isAbleToJumpInDeadend(initialAction, x, y, direction, newSpeed, newX, newY):
                    self.logActionValue[0][initialAction] += self.deadendBias
                self.jobQueue.put((self.checkChoices, [newX, newY, direction, newSpeed, depth + 1,
                                                       initialAction, newActionCoord, distance - newSpeed, 0,
                                                       checkCounter]))

    def checkLeftorRight(self, x, y, direction, speed, depth, action, coord, distance, collCounter,
                         checkCounter, change):
        """
        Check if the action left/right is possible. If it is possible,
        add the value for the current depth to logActionValue and add all 5 sub-actions to the Queue

        :param x: the coordinate x of the snakes' head
        :param y: the coordinate y of the snakes' head
        :param direction: the direction the snake is headed
        :param speed: with what speed the snake is going (0<speed<11)
        :param depth: the current depth of how deep the snake checked its moves
        :param action: the action on which this move is first based
        :param coord: a list of coordinates, where the snake already was. Used to prevent hitting itself
        :param distance: the number of free fields in the current direction
        :param collCounter: number of consecutive turns in a specific direction
        :param checkCounter: number of turns in general
        :param change: Either "left" or "right". Determines which direction should be checked
        :return: returns if move is not possible
        """
        coordIgnore = checkCounter < 2  # True, if coords doesn't have to be checked, because snake didn't turn twice
        direction = getNewDirection(direction, change)
        isJumping = self.counter % 6 == 0
        newcoord = coord[:]

        newheadY, newheadX = getNewPos(x, y, speed, direction)
        if (change == "left" and collCounter != -2 or change == "right" and collCounter != 2) \
                and self.isValid(newheadX, newheadY, coordIgnore, coord):
            newcoord.append([newheadY, newheadX])
            for i in range(1, speed):
                if isJumping:  # If it is the sixth round, skip the occuring gap
                    newbodyY, newbodyX = getNewPos(x, y, 1, direction)
                    if not self.isValid(newbodyX, newbodyY, coordIgnore, coord):
                        return
                    newcoord.append([newbodyY, newbodyX])
                    break
                newbodyY, newbodyX = getNewPos(x, y, i, direction)
                if not self.isValid(newbodyX, newbodyY, coordIgnore, coord):
                    return
                newcoord.append([newbodyY, newbodyX])
            self.logActionValue[depth][action] += self.value
            if self.isAbleToJumpInDeadend(action, x, y, direction, speed, newheadX, newheadY):
                self.logActionValue[0][action] += self.deadendBias
            if change == "left":
                if collCounter <= 0:
                    checkCounter += 1
                collCounter = min(collCounter - 1, - 1)
            else:
                if collCounter >= 0:
                    checkCounter += 1
                collCounter = max(collCounter + 1, 1)

            if distance == 0 and coordIgnore:
                distance = self.getDistance(newheadX, newheadY, direction)[0] + speed

            self.jobQueue.put((self.checkChoices, [newheadX, newheadY, direction, speed, depth + 1,
                                                   action, newcoord, distance - speed, collCounter, checkCounter]))

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
        return dis, x, y

    def checkChoices(self, x, y, direction, speed, depth, action, coord, distance,
                     collCounter, checkCounter):
        """
        First, check if less than a second to the deadline is left. If so, drop the Queue and return
        If not, check if a new layer has been reached. Then call functions to check the 5 actions

        :param x: the coordinate x of the snakes' head
        :param y: the coordinate y of the snakes' head
        :param direction: the direction the snake is headed
        :param speed: with what speed the snake is going (0<speed<11)
        :param depth: the current depth of how deep the snake checked its moves
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
        self.checkFront(x, y, direction, speed, depth, action, coord, distance, checkCounter)

        # Check-Left
        self.checkLeftorRight(x, y, direction, speed, depth, action, coord, 0, collCounter, checkCounter, "left")

        # Check-Right
        self.checkLeftorRight(x, y, direction, speed, depth, action, coord, 0, collCounter, checkCounter, "right")

    def freeLR(self, x, y, direction):
        """
        checks, whether the fields left and right of a specific coordinate and direction are blocked

        :param x: x coordinate
        :param y: y coordinate
        :param direction: direction of player
        :return: True if at least one field to the side of the coordinates and direction is empty, False otherwise
        """
        freeLeft = False
        ly, lx = getNewPos(x, y, 1, getNewDirection(direction, "left"))
        if self.isInBound(lx, ly) and self.board[ly][lx] == 0:
            freeLeft = True

        freeRight = False
        ry, rx = getNewPos(x, y, 1, getNewDirection(direction, "right"))
        if self.isInBound(rx, ry) and self.board[ry][rx] == 0:
            freeLeft = True

        return freeLeft or freeRight

    # computes the maximum distance to the left and right of a direction and coordinates
    def maxLR(self, x, y, direction):
        """
        computes the maximum distance to the left or right of specific coordinates and a specific direction
        if the last coordinates in a direction does not allow for further moves,
        it continues with the coordinates and distance to the coordinates before that

        :param x: x coordinates
        :param y: y coordinates
        :param direction: direction of player
        :return: maximum distance to the left/right of specific coordinates and specific direction
        """
        distances = []
        for LoR in ["left", "right"]:

            pDirection = getNewDirection(direction, LoR)
            dis, px, py = self.getDistance(x, y, pDirection)

            isFreeL = self.freeLR(px, py, pDirection)
            while isFreeL == 0 and dis > 0:  # if maxLR == 0: check one step back
                px, py, dis = discardImpasse(px, py, dis, pDirection)
                isFreeL = self.freeLR(px, py, pDirection)
            distances.append(dis)
        return max(distances)

    # computes the maximum possible number of fields in one direction including one turn at the end
    def checkDeadend(self, x, y, direction, limitIndex):
        """
        computes the T distance in all directions
        if the last coordinate in the direction does not allow for further moves,
        it continues with the coordinates before that
        If the T distance is bigger than the given limitIndex, return it

        :param x: x coordinate
        :param y: y coordinate
        :param direction: direction of player
        :param limitIndex: 1: test until deadendLimit, 0: test until safeZoneLimit
        :return: biggest T distance
        """
        result = 0
        limit = [self.safeZoneLimit, self.deadendLimit][limitIndex]
        for newDir in [direction, getNewDirection(direction, "left"), getNewDirection(direction, "right")]:
            dis, px, py = self.getDistance(x, y, newDir)
            LR = self.maxLR(px, py, newDir)
            while LR == 0 and dis > 0:  # if maxLR == 0: check one step back
                px, py, dis = discardImpasse(px, py, dis, newDir)
                LR = self.maxLR(px, py, newDir)
            if dis + LR > limit:
                return dis + LR
            elif dis + LR > result:
                result = dis + LR
        return result

    def checkNewLayer(self, depth):
        """
        If logActionValue is not longer than the depth, append it, and update some variables for the new layer

        :param depth: the level on which the snake checks the possible moves
        """
        if not len(self.logActionValue) > depth:
            self.logActionValue.append([0, 0, 0, 0, 0])
            self.value = self.value * self.gamma
            self.counter = self.roundNumber + depth

    def checkDeadline(self):
        """
        :return: Drop the Queue and return, if less than the timePuffer remains to the deadline
                and he checked more than 4 layers
        """
        if time.time() + self.timePuffer + self.ping > self.deadline:
            if len(self.logActionValue) > 4:
                with self.jobQueue.mutex:
                    self.jobQueue.queue.clear()
                return True
        return False

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
                    pathListFront = [0] * newSpeed
                    pathListFront[0] = 7
                    pathListFront[-1] = 7
                    pathListFront[-2] = 7

                    pathListSides = [0] * (newSpeed - 1 * speedNotTen)
                    pathListSides[0] = 7
                    pathListSides[-1] = 7

                    if newSpeed >= 3:
                        pathListFront[-3] = 7
                else:
                    pathListFront = [7] * newSpeed
                    pathListSides = [7] * (newSpeed - 1 * speedNotTen)

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

                    chosenPath = [pathListFront, pathListSides][pathNum]
                    numberSteps = int(numberSteps)
                    for step in range(1, numberSteps + 1):
                        stepX = enemyObject["x"] + stepVector[1] * step
                        stepY = enemyObject["y"] + stepVector[0] * step
                        enemyBoard[int(stepY)][int(stepX)] = max(chosenPath[step - 1],
                                                                 enemyBoard[int(stepY)][int(stepX)])
                    pathNum = 1
        return enemyBoard

    def gameStep(self, state):
        """
        Will be called in every step to initialize different variables as well as start the process of checking every
        possible action

        :param state: given state by the server
        :return: returns the action that should be played as well as other variables that may be needed for the GUI
        """
        # Initialization
        depth = 0
        self.roundNumber += 1
        self.counter = self.roundNumber
        self.value = 1
        isJumping = self.roundNumber % 6 == 0
        self.logActionValue = [[0, 0, 0, 0, 0]]
        self.deadline = dp.parse(state["deadline"]).timestamp()
        executedJobs = 0  # Debugging

        # create a board, which includes every next move of the active enemies
        # also includes moves leading to a potential death of an enemy
        self.board = self.constructEnemyBoard(state, isJumping)

        own = state["players"][str(state["you"])]

        de = self.checkDeadend(own["x"], own["y"], own["direction"], 0)

        self.isDeadend = de < self.deadendLimit
        self.isSafeZone = de > self.safeZoneLimit and getMinimalEnemyDistance(state, own["x"],
                                                                              own["y"]) > self.safeZoneDistance

        # Catches the special case, when the possible moves of an enemy blocks our snake. We will then proceed
        # with the basic board, that doesn´t have the enemies' possible moves included
        while True:
            # check the unoccupied distance in all directions
            straightDistance, sx, sy = self.getDistance(own["x"], own["y"], own["direction"])
            leftDistance, lx, ly = self.getDistance(own["x"], own["y"], getNewDirection(own["direction"], "left"))
            rightDistance, rx, ry = self.getDistance(own["x"], own["y"], getNewDirection(own["direction"], "right"))

            # check-sd/cn/su
            self.checkFront(own["x"], own["y"], own["direction"], own["speed"], depth,
                            None, [], straightDistance, 0)

            # check-left
            self.checkLeftorRight(own["x"], own["y"], own["direction"], own["speed"], depth,
                                  3, [], leftDistance, 0, 0, "left")

            # check-right
            self.checkLeftorRight(own["x"], own["y"], own["direction"], own["speed"], depth,
                                  4, [], rightDistance, 0, 0, "right")

            # works on objects in the queue until it is either empty or the deadline is close
            while not self.jobQueue.empty():
                executedJobs += 1  # Debugging
                f, args = self.jobQueue.get()
                f(*args)

            if len(self.logActionValue) > 1:
                break

            # if there are no possible move, when the first moves of the enemies are accounted for, they are discarded
            self.board = state["cells"]

        indexAction, choices = self.calcAction()
        return indexAction, choices, de, self.isDeadend, executedJobs, len(self.logActionValue), self.roundNumber, \
               self.isSafeZone, self.deadline
