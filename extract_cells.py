import time
import pyautogui
import cv2
import numpy as np
import os

def extract_cells():

    print("Ai 10 secunde să deschizi fereastra cu Minesweeper...")
    time.sleep(10)


    tabla_x = 105
    tabla_y = 310


    latime_celula = 24
    inaltime_celula = 24
    nr_randuri = 9
    nr_coloane = 9


    screenshot = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


    for rand in range(nr_randuri):
        for coloana in range(nr_coloane):
            x = tabla_x + coloana * latime_celula
            y = tabla_y + rand * inaltime_celula
            
            celula = img[y:y+inaltime_celula, x:x+latime_celula]
            path = f"cells/cell_{rand}_{coloana}.png"
            cv2.imwrite(path, celula)

