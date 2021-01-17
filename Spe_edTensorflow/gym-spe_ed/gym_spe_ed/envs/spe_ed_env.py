from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc
import tensorflow as tf
import numpy as np
from enum import Enum
import random
import gym
from gym import error, spaces, utils
from gym.utils import seeding
import copy


class Board():
    def __init__(self, w, h):
        self.board = [[0]*w for _ in range(h)]
        self.gameColl = []

    def takeField(self, p, w, h):
        if self.board[h][w] == 0:
            self.board[h][w] = p.n
            return True
        elif not self.board[h][w] == 0:
            return False

    def fieldTaken(self, w, h):
        if self.board[h][w] == 0:
            return False
        elif not self.board[h][w] == 0:
            return True
    
    def addColl(self, w, h):
        self.board[h][w] = -1       
 

class Player():
    def __init__(self, n, x, y):
        self.n = n
        self.x = x
        self.y = y
        self.alive = True
        self.speed = 1
        self.direction = random.choice(list(Direction))
        self.nextSteps = []

class PlayerBot(Player):
    def __init__(self, n, x, y, KI):
        super().__init__(n, x, y)
        self.KI = KI

class Action(Enum):
    CHANGE_NOTHING = 0
    RIGHT = 1
    LEFT = 2
    SPEED_UP = 3
    SPEED_DOWN = 4

class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2 
    WEST = 3

class Spe_edEnv(gym.Env):

    def __init__(self):
        super().__init__()
        self.reset()
        high = len(self.playerBots) + 1
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(low = 0, high = high, 
            shape=(17,17,3), dtype=np.int32)
    

    def reset(self):
        self.board = Board(10, 10)
        self.playerBots = []
        self.player = Player(1, random.randint(0, len(self.board.board[0])-1), random.randint(0, len(self.board.board)-1))
        self.state = np.zeros((len(self.board.board), len(self.board.board[0]), 2), dtype=np.int32)
        self.init_board()
        self.gameRound = 1
        return self.adjustState([self.player.y,self.player.x], 17)

    def render(self):
	    print(np.moveaxis(self.adjustState([self.player.y,self.player.x], 17), -1, 0)[0])	
    
    def init_board(self):
        self.board.takeField(self.player, self.player.x, self.player.y)
        botNumber = random.randint(1,2)
        for bot in range(botNumber):
            newBot = PlayerBot(1, random.randint(0, len(self.board.board[0])-1), random.randint(0, len(self.board.board)-1), self.randKI)
            taken = not self.board.takeField(newBot, newBot.x, newBot.y)
            while taken:
                newBot.x = random.randint(0, len(self.board.board[0])-1)
                newBot.y = random.randint(0, len(self.board.board)-1)
                taken = not self.board.takeField(newBot, newBot.x, newBot.y)
            self.playerBots.append(newBot)
        self.state = np.insert(self.state, 0, self.board.board, axis=2)


    def move(self, player, action):
        if action == Action.RIGHT:
            self.calc_NewDir(player, [Direction.EAST, Direction.SOUTH, Direction.WEST, Direction.NORTH])
        elif action == Action.LEFT:
            self.calc_NewDir(player, [Direction.WEST, Direction.NORTH, Direction.EAST, Direction.SOUTH])
        elif action == Action.SPEED_UP and player.speed < 10:
            player.speed += 1
        elif action == Action.SPEED_DOWN and player.speed > 1:
             player.speed -= 1
        self.calc_NewCoords(player)

    def calc_NewCoords(self, player):
        jumpPoints = player.speed - 2

        if player.direction == Direction.NORTH:
            for i in range(player.speed):
                if self.gameRound == 6 and player.speed > 2 and i > 0 and jumpPoints > 0:
                    jumpPoints = jumpPoints-1
                else:
                    player.nextSteps.append((player.x, player.y-1-i))

        elif player.direction == Direction.EAST:
            for i in range(player.speed):
                if self.gameRound == 6 and player.speed > 2 and i > 0 and jumpPoints > 0:
                    jumpPoints = jumpPoints-1
                else:
                    player.nextSteps.append((player.x+1+i, player.y))          

        elif player.direction == Direction.SOUTH:
            for i in range(player.speed):
                if self.gameRound == 6 and player.speed > 2 and i > 0 and jumpPoints > 0:
                    jumpPoints = jumpPoints-1
                else:
                    player.nextSteps.append((player.x, player.y+1+i))   

        elif player.direction == Direction.WEST:
            for i in range(player.speed):
                if self.gameRound == 6 and player.speed > 2 and i > 0 and jumpPoints > 0:
                    jumpPoints = jumpPoints-1
                else:
                    player.nextSteps.append((player.x-1-i, player.y))   

    def calc_NewDir(self, player ,dir_List):
        if player.direction == Direction.NORTH:
            player.direction = dir_List[0]
        elif player.direction == Direction.EAST:
            player.direction = dir_List[1]
        elif player.direction == Direction.SOUTH:
            player.direction = dir_List[2]
        elif player.direction == Direction.WEST:
            player.direction = dir_List[3]

    def face_Control(self, coord, player):
        x_Check = coord[0] < 0 or coord[0] >= len(self.board.board[0])
        y_Check = coord[1] < 0 or coord[1] >= len(self.board.board)
        if x_Check or y_Check:
            return False
        else:
            return True

    def game_Step(self, playerAction):
        if self.player.alive:
            self.move(self.player, playerAction)
        for bot in self.playerBots + [self.player]:
            if bot.alive and bot != self.player:
                self.move(bot, bot.KI(bot))
            bot.alive = bot.alive and self.checkPath(bot)
            if len(bot.nextSteps) > 0:
                bot.x = bot.nextSteps[len(bot.nextSteps)-1][0]
                bot.y = bot.nextSteps[len(bot.nextSteps)-1][1]
            
        for bot in self.playerBots + [self.player]:
            for step in bot.nextSteps:
                self.board.takeField(bot, step[0], step[1])
            coll = self.checkIntersections(bot)
            if not (coll == None):
                bot.alive = False
                self.board.addColl(coll[0][0], coll[0][1])

        for bot in self.playerBots + [self.player]:
                bot.nextSteps.clear()

        if self.gameRound >= 6:
            self.gameRound = 1
        else:
            self.gameRound += 1
        self.state = np.insert(self.state, 0, self.board.board, axis=2)	
        self.state = np.delete(self.state, 3, axis=2)

    def checkPath(self, bot):
        for step in bot.nextSteps:
                validStep = self.checkStep(bot, step)
                if not validStep:
                    index = bot.nextSteps.index(step)
                    bot.nextSteps = bot.nextSteps[:index]
                    return False
        return True


    def checkStep(self, bot, step):
            if(self.face_Control(step, bot)):
                return not self.board.fieldTaken(step[0], step[1])
            else:
                return False

    def checkIntersections(self, bot):
        for enemy in self.playerBots + [self.player]:
            if bot != enemy and bot.alive:
                collEnemy = (set(bot.nextSteps).intersection(enemy.nextSteps))

                if len(collEnemy) != 0:
                    return list(collEnemy)

    def print_Board(self):
        print(self.gameRound)
        for i in range(40):
            print(i%10, " ", end='')

        print()
        for i in board.board:
            for ii in i:
                print(ii," ", end = '')
            print()
        print()

    def randKI(self, bot):
        return self.plepKI(bot)

    def plepKI(self, bot):
        botCopy = copy.deepcopy(bot)
        ActionList = self.checkAllActions(botCopy, 3)
        act = ActionList.index(max(ActionList))
        return Action(act)

    def checkAllActions(self, bot, deep):
        ActionList = [0,0,0,0,0]
        botX = bot.x
        botY = bot.y
        botSpeed = bot.speed
        botDirection = bot.direction
        for actNumber in range(len(ActionList)):
            bot.x = botX
            bot.y = botY
            bot.speed = botSpeed
            bot.direction = botDirection
            act = Action(actNumber)
            self.move(bot, act)
            if self.checkPath(bot):
                bot.x = bot.nextSteps[len(bot.nextSteps)-1][0]
                bot.y = bot.nextSteps[len(bot.nextSteps)-1][1]
                bot.nextSteps.clear()
                ActionList[actNumber] = 1 + self.takeActionList(bot, deep-1)
            bot.nextSteps.clear()
        return ActionList

    def takeActionList(self, bot, deep):
        botX = bot.x
        botY = bot.y
        botSpeed = bot.speed
        botDirection = bot.direction
        ActionList = [0,0,0,0,0]
        if deep <= 0:
            return 0
        for actNumber in range(len(ActionList)):
            bot.x = botX
            bot.y = botY
            bot.speed = botSpeed
            bot.direction = botDirection
            act = Action(actNumber)
            self.move(bot, act)
            if self.checkPath(bot):
                ActionList[actNumber] +=1
                bot.x = bot.nextSteps[len(bot.nextSteps)-1][0]
                bot.y = bot.nextSteps[len(bot.nextSteps)-1][1]
                bot.nextSteps.clear()
                if deep > 0:
                    ActionList[actNumber] = 1 + self.takeActionList(bot, deep-1)
                else:
                    ActionList[actNumber] =+ 1
        return max(ActionList)

    def step(self, action):
        self.game_Step(Action(action))
        if self.player.alive:
	        return self.adjustState([self.player.y,self.player.x], 17), 1, False, {}
        else:
	        return self.adjustState([self.player.y,self.player.x], 17), -1, True, {}

    def adjustState(self, head, width):
        rad = (width-1)//2
        upLeft = [head[0]-rad, head[1]- rad]
        out = [[[1 for b in range(3)] for i in range(width)] for j in range(width)] #
        for b in range(3):	
            for i in range(width):	
                if i+upLeft[0] >= 0 and i+upLeft[0] < len(self.board.board):	
                    for j in range(width):	
                        if j+upLeft[1] >= 0 and j+upLeft[1] < len(self.board.board[0]):	
                            out[i][j][b] = self.state[i+upLeft[0]][j+upLeft[1]][b]	

        out = np.array(out)	
        if self.player.direction != Direction.NORTH:	
            out = np.rot90(out)	
            if self.player.direction == Direction.SOUTH or self.player.direction == Direction.WEST:	
                out = np.rot90(out)	
                if self.player.direction == Direction.WEST:	
                    out = np.rot90(out)	
        
        return np.array(out)
