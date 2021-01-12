import calendar
from datetime import datetime, date
import time
import json
from copy import deepcopy, copy
from enum import Enum
from queue import Queue
from threading import Thread
from collections import deque
import matplotlib.pylab as plt
# from matplotlib import pyplot
from matplotlib import pyplot, use, colors
from scipy import sparse
import dateutil.parser as dp

global q
global ebene
global notbremse
global myc

def getnewdirection(dir, change):  # bestimme neue Richtung nach Wechsel
    if dir == change:
        return "down"
    if change == "left":
        if dir == "up":
            return "left"
        elif dir == "down":
            return "right"
        else:
            return "up"
    else:
        if dir == "down":
            return "left"
        elif dir == "up":
            return "right"
        else:
            return "up"


def getnewpos(x, y, s, dir):  # bestimme neue Position
    if dir == "up":
        return [y - s, x]
    elif dir == "down":
        return [y + s, x]
    elif dir == "left":
        return [y, x - s]
    elif dir == "right":
        return [y, x + s]


class Direction(Enum):
    Up = 0
    Down = 1
    Left = 2
    Right = 3


def checkLeft(x,y,direction, board, speed, width, height, wert, depth, counter, deadline, action,coord, collCounter, checkCounter):
    isJump = False
    newcoord3 = coord[:]
    newdirection = getnewdirection(direction, "left")
    newy, newx = getnewpos(x, y, speed, newdirection)
    if height > newy >= 0 and width > newx >= 0 and board[newy][newx] == 0:
        hit = False
        newcoord3.append([newy, newx])
        for i in range(1, speed):
            if isJump:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                newyy, newxx = getnewpos(x, y, 1, newdirection)
                if board[newyy][newxx] != 0:
                    hit = True
                    break
                newcoord3.append([newyy, newxx])
                break
            newyy, newxx = getnewpos(x, y, i, newdirection)
            if board[newyy][newxx] != 0:
                hit = True
                break
            newcoord3.append([newyy, newxx])
        if not hit:
            ebene[depth][action] += wert
            q.put((checkchoices, [newx, newy, newdirection, board, speed, width, height, wert / 2,
                                  depth + 1, counter + 1, deadline, action, newcoord3, min(collCounter - 1, - 1),
                                  checkCounter - 1]))

def checkchoices(x, y, direction, board, speed, width, height, wert, depth, counter, deadline, action):

    global ebene
    global q
    global notbremse
    global myc

    myc = depth

    if not len(ebene) > depth:
        ebene.append([0, 0, 0, 0, 0])

    #   Bei Jahreswechsel kann es zu Fehlern (zu kurzen Berechnungen) kommen..
    #   Auch so kann es sein, dass die ersten Berechnungen noch durchkommen, der Rest aber nicht mehr

    current_time = str(datetime.utcnow())
    mo = int(current_time[5:7])
    t = int(current_time[8:10])
    h = int(current_time[11:13])
    m = int(current_time[14:16])
    s = int(current_time[17:19])
    ctime = (((mo * 30 + t) * 24 + h) * 60 + m) * 60 + s

    # Wenn weniger als eine Sekunde bis zur Deadline verbleibt, bearbeite die Queue nicht weiter
    if ctime + 1 > deadline:
        notbremse = True
        print(depth)
        return

    # werden verwendet, um Ressourcen bei zu schonen, da nurnoch Kopf geprüft werden muss, wenn voriges geprüft wurde
    clearsd = False
    clearcn = False

    # check-slowdown
    newboard = deepcopy(board)
    if speed > 1:
        newpos = getnewpos(x, y, speed - 1, direction)
        newx = newpos[1]
        newy = newpos[0]
        if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                newboard[newy][newx] = 7
                hit = False
                for i in range(1, speed - 1):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newpos = getnewpos(x, y, 1, direction)
                        newxx = newpos[1]
                        newyy = newpos[0]
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        newboard[newyy][newxx] = 7
                        break
                    newpos = getnewpos(x, y, i, direction)
                    newxx = newpos[1]
                    newyy = newpos[0]

                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                if not hit:
                    clearsd = True
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, direction, newboard, speed - 1, width, height, wert / 2, depth + 1, counter + 1, deadline, action]))

    # check-nothing
    if not clearsd:
        newboard = deepcopy(board)
    newpos = getnewpos(x, y, speed, direction)
    newx = newpos[1]
    newy = newpos[0]
    if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
        if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
            newboard[newy][newx] = 7
            hit = False
            for i in range(1, speed):
                if clearsd:
                    break
                if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                    newpos = getnewpos(x, y, 1, direction)
                    newxx = newpos[1]
                    newyy = newpos[0]
                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                    break
                newpos = getnewpos(x, y, i, direction)
                newxx = newpos[1]
                newyy = newpos[0]

                if not board[newyy][newxx] == 0:
                    hit = True
                    break
                newboard[newyy][newxx] = 7
            if not hit:
                clearcn = True
                ebene[depth][action] += wert
                q.put((checkchoices, [newx, newy, direction, newboard, speed, width, height, wert / 2,depth + 1, counter + 1, deadline, action]))

    # check-speedup
    if not clearcn:
        newboard = deepcopy(board)
    if speed < 10:
        newpos = getnewpos(x, y, speed + 1, direction)
        newx = newpos[1]
        newy = newpos[0]
        if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                hit = False
                newboard[newy][newx] = 7
                for i in range(1, speed + 1):
                    if clearcn:
                        break
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newpos = getnewpos(x, y, 1, direction)
                        newxx = newpos[1]
                        newyy = newpos[0]
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        newboard[newyy][newxx] = 7
                        break
                    newpos = getnewpos(x, y, i, direction)
                    newxx = newpos[1]
                    newyy = newpos[0]

                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][
                        newxx] = 7
                if not hit:
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, direction, newboard, speed + 1, width, height, wert / 2,depth + 1, counter + 1, deadline, action]))

    # check-left and check-right
    for newd in ["left", "right"]:
        newboard = deepcopy(board)
        newdirection = getnewdirection(direction, newd)
        newpos = getnewpos(x, y, speed, newdirection)
        newx = newpos[1]
        newy = newpos[0]
        if height - 1 >= newy >= 0 and width - 1 >= newx >= 0:  # Prüfe ob er das Spielfeld verlassen würde
            if board[newy][newx] == 0:  # Prüfe ob Schlange an den neuen Stelle sind
                newboard[newy][newx] = 7
                hit = False
                for i in range(1, speed):
                    if counter % 6 == 0:  # Prüfe ob sechste runde und dann prüfe nicht Lücke
                        newpos = getnewpos(x, y, 1, newdirection)
                        newxx = newpos[1]
                        newyy = newpos[0]
                        if not board[newyy][newxx] == 0:
                            hit = True
                            break
                        newboard[newyy][newxx] = 7
                        break
                    newpos = getnewpos(x, y, i, newdirection)
                    newxx = newpos[1]
                    newyy = newpos[0]

                    if not board[newyy][newxx] == 0:
                        hit = True
                        break
                    newboard[newyy][newxx] = 7
                if not hit:
                    ebene[depth][action] += wert
                    q.put((checkchoices, [newx, newy, newdirection, newboard, speed, width, height, wert / 2,depth + 1, counter + 1, deadline, action]))



def testmethode(wert, counter, deadline, action):
    #print(counter)

    global ebene
    if not len(ebene) > counter:
        ebene.append([0,0,0,0,0])
    ebene[counter][action] += wert

    time.sleep(0.01)
    global q
    if time.time() > deadline:
        ebene[counter][action] = -1
        global notbremse
        notbremse = True
        return
    else:
        #q.put("testmethode(" + str(wert / 2) + "," + str(counter + 1) + "," + str(deadline) + "," + str(action) + ")")
        q.put((testmethode,[wert / 2, counter + 1, deadline, action]))
        q.put((testmethode,[wert / 2, counter + 1, deadline, action]))
        q.put((testmethode,[wert / 2, counter + 1, deadline, action]))
        q.put((testmethode,[wert / 2, counter + 1, deadline, action]))
        q.put((testmethode,[wert / 2, counter + 1, deadline, action]))



def main():
    state = {'width': 62, 'height': 43, 'cells':
        [
            [0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
             3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], 'players': {
        '1': {'x': 34, 'y': 9, 'direction': 'right', 'speed': 6, 'active': True},
        '2': {'x': 18, 'y': 0, 'direction': 'down', 'speed': 1, 'active': False},
        '3': {'x': 22, 'y': 12, 'direction': 'left', 'speed': 1, 'active': True}}, 'you': 1, 'running': True,
             'deadline': '2020-10-19T13:20:18Z'}

    own_player = state["players"][str(state["you"])]
    # global ebene
    # ebene = [[0,0,0,0,0]]
    # global q
    # q= Queue
    # state2 = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]*150
    # print(state2)
    # checkchoices(75,75,"up",state2,5,150,150,1,0,1,time.time()+60,2)
    # while not q.empty:
    #     f, args = q.get()
    #     f(*args)
    # print(ebene)
    # newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"], own_player["direction"])
    # print(state["cells"][69][66])
    # if ([state["width"] - 1, state["height"] - 1] <= newpos):            #& (newpos >= [0, 0]):
    # print("yo")
    # print(own_player["speed"])
    # print(own_player["direction"])
    hilfe = 0
    # for i in range(1, own_player["speed"]):
    #     newpos = getnewpos(own_player["x"], own_player["y"], own_player["speed"],
    #                        getnewdirection(own_player["direction"], "right"))
    #     print(newpos)
    #     newx = newpos[1]
    #     newy = newpos[0]
    #     if not state["cells"][newy][newx] == 0:
    #         print("ficken")
    # if hilfe == 0:
    #     print("fuck")
    # print(datetime.now())
    # board1 = deepcopy(board)
    # board2 = deepcopy(board)
    # board3 = deepcopy(board)
    # board4 = deepcopy(board)
    # board5 = deepcopy(board)
    # print(datetime.now())
    # print(time.time())
    # deadline = "2020-12-14T16:28:10Z"
    # cteim = str(datetime.now())
    # print(state["players"]["3"]["active"])
    # wert = 1
    # counter = 0
    # deadline = time.time()+5
    # choices = [0,0,0,0,0]
    # global ebene
    # ebene = [[1,1,1,1,1]]
    # global q
    # q = Queue()
    # # #
    # q.put("testmethode("+str(wert/2)+","+str(counter+1)+","+str(deadline)+",0)")
    # q.put(testmethode(wert / 2, counter + 1, deadline, 0))
    # q.put((testmethode,[wert/2,counter+1,deadline,1]))
    # q.put((testmethode,[wert / 2, counter + 1, deadline, 2]))
    # q.put((testmethode,[wert / 2, counter + 1, deadline, 3]))
    # q.put((testmethode,[wert / 2, counter + 1, deadline, 4]))
    #
    # global notbremse
    # notbremse = False
    # while not q.empty():
    #     #print(q.get())
    #     f,args = q.get()
    #     f(*args)
    #     if notbremse:
    #         break



    # you = str(state["players"][str(state["you"])])
    # counter = 3
    # choices = [0,0,0,0,0]
    # action = "turn"
    # board = state["cells"]
    # w = state["width"]/10
    # h = (state["height"]/10)+0.5
    # for p in range(1, int(len(state["players"]) + 1)):
    #     board[state["players"][str(p)]["y"]][state["players"][str(p)]["x"]] = -1
    #
    # with pyplot.xkcd():
    #     pyplot.figure(figsize=(w,h))
    #     colormap = colors.ListedColormap(["black", "green","white","blue", "yellow", "red", "cyan", "magenta", "grey"])
    #     pyplot.imshow(board, cmap=colormap)
    #     pyplot.title("Runde: " + str(counter))
    #     pyplot.xticks([])
    #     pyplot.yticks([])
    #     pyplot.xlabel(you + "\n" + str(choices) + "\n" + "nächster Zug: " + str(action))
    #     pyplot.show(block=False)
    x=30
    y=34
    counter = 6
    an = time.time()
    board = state["cells"]
    actionlist = [0,4,2,4,1,1,0,2,3,4,1,3]
    coord = [[34,15],[12,55],[14,58],[1,1],[12,58],[13,37],[4,20],[10,10],[18,21],[88,88],[153,12],[158,4],[24,41],[11,42],[24,42],[11,7],[34,15],[12,55],[14,54],[1,1],[12,58],[13,37],[4,20],[34,15],[12,55],[14,58],[1,1],[12,58],[13,37],[4,20],[10,10],[18,21],[88,88],[153,12],[158,4],[24,41],[11,42],[24,42],[11,7],[34,15],[12,55],[14,54],[1,1],[12,58],[13,37],[4,20]]
    isCC = True
    direction = own_player["direction"]
    width = state["width"]
    height = state["height"]
    speed = own_player["speed"]
    isJump = False
    wert = 0.5
    depth = 1
    deadline = 4
    action = 3
    collCounter = 0
    checkCounter = 0
    global ebene
    ebene = [[0,0,0,0,0],[0,0,0,0,0]]
    global q
    q = Queue()
    change = "left"

    test = [[12,54],[13,54],[14,14]]        #,[15,54],[16,54],[17,54]
    for i in range(1,100000000):
        if change == "left":
            x = 3

    print(4.050813913345337-4.323548078536987)
    # 0.3964817523956299
    # print(state["cells"])
    # print(neu)
    # 100k kopien: deepcopy116 sek, map und row 1.1 sek,
    # print(sum)
    # print(sum[5])
    coord = [[1,2],[3,4],[5,6]]
    newcoord = coord[:]
    newcoord.append([13,37])
    test = newcoord
    newcoord = coord[:]
    print(time.time() - an)
    # gesamt = 0
    # anzahl = 0
    # list = []
    # listende = []
    # for i in range(0,5):
    #     for ii in range(0, 5):
    #         for iii in range(0, 5):
    #             for iv in range(0, 5):
    #                 for v in range(0, 5):
    #                     for vi in range(0, 5):
    #                         for vii in range(0, 5):
    #                             for viii in range(0, 5):
    #                                 for ix in range(0, 5):
    #                                     for x in range(0, 5):
    #                                         gesamt += 1
    #                                         test = [i,ii,iii,iv,v,vi,vii,viii,ix,x]
    #                                         if test.count(4) > 1:
    #                                             list.append(test)
    # for i in range(0,len(list)):
    #     if list[i][list[i].index(4)+1] == 4:
    #         listende.append(list[i])
    # # print(list[0][list.index(4)])
    # print(listende)
    # # print(anzahl)
    # print(len(listende)/gesamt)
    # print(anzahl/gesamt)
    # deadline = str(datetime.utcnow())
    # print(deadline)
    # deadline = "2021-01-04T12:04:23Z"
    # #print(current_time)
    # ja = int(deadline[0:4])-2021
    # mo = int(deadline[5:7])
    # t = int(deadline[8:10])
    # h = int(deadline[11:13])
    # m = int(deadline[14:16])
    # s = int(deadline[17:19])
    # ctime = (((((ja*12)+mo-1) * 30 + t-1) * 24 + h) * 60 + m) * 60 + s
    # print(state["deadline"])
    #
    # jahre = 1609459200
    # print(jahre+ctime)
    #
    # t = '2021-01-04T12:04:23Z'
    # parsed_t = dp.parse(t).timestamp()
    # print(parsed_t)


main()

