from datetime import datetime, date
import time
import json
from copy import deepcopy
from queue import Queue
from threading import Thread
from collections import deque
import matplotlib.pylab as plt
# from matplotlib import pyplot
from matplotlib import pyplot, use, colors
from scipy import sparse

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
main()
