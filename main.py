import time
import pyautogui
import cv2
import numpy as np
import os
import sys
import random


# Variabile globale pentru dimensiunile tablei
tabla_x = 0
tabla_y = 0
latime_celula = 24
inaltime_celula = 24


def detecteaza_stare_joc():
    """
    Returnează starea jocului Minesweeper analizând smiley face-ul:
    - 'playing'
    - 'won'
    - 'lost'
    - None dacă nu se poate determina
    """

    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Șabloane
    templates = {
        'playing': cv2.imread('smiley/play.png'),
        'won': cv2.imread('smiley/win.png'),
        'lost': cv2.imread('smiley/lose.png')
    }

    # Căutăm fiecare șablon în screenshot
    for stare, template in templates.items():
        if template is None:
            print(f"[WARN] Șablonul {stare} nu a fost găsit!")
            continue

        res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        if max_val >= 0.95:
            return stare

    return None

def gaseste_tabla_info(template_path="./templates/unknow.png", threshold=0.97):
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    h, w = template.shape[:2]

    rezultat = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    locuri = np.where(rezultat >= threshold)

    puncte = list(zip(*locuri[::-1]))  # (x, y)

    if not puncte:
        raise Exception("Nu s-au găsit celule.")

    # Sortează punctele după Y, apoi X
    puncte = sorted(puncte, key=lambda p: (p[1], p[0]))

    # Grupuiește rândurile după distanța verticală
    randuri = []
    dist_y = h // 2
    for p in puncte:
        gasit = False
        for rand in randuri:
            if abs(rand[0][1] - p[1]) < dist_y:
                rand.append(p)
                gasit = True
                break
        if not gasit:
            randuri.append([p])

    # Sortează fiecare rând după X (coloane)
    for rand in randuri:
        rand.sort(key=lambda p: p[0])

    nr_randuri = len(randuri)
    nr_coloane = max(len(rand) for rand in randuri)
    colt_stanga_sus = randuri[0][0]  

 
    return nr_randuri, nr_coloane, colt_stanga_sus

def identifica_celula(img_celula, templates_dir="templates"):
    """Identifică tipul unei celule comparând cu template-uri"""
    if not os.path.exists(templates_dir):
        print(f"[EROARE] Folderul {templates_dir} nu există!")
        return "necunoscut"
    
    max_score = -1
    label_final = "necunoscut"
    
    for filename in os.listdir(templates_dir):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
            
        template = cv2.imread(os.path.join(templates_dir, filename))
        if template is None:
            continue
        
        template = cv2.resize(template, (img_celula.shape[1], img_celula.shape[0]))
        res = cv2.matchTemplate(img_celula, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(res)
        
        nume_template = os.path.splitext(filename)[0]
        
        if score > max_score:
            max_score = score
            label_final = nume_template
    
    return label_final if max_score > 0.85 else "necunoscut"

def extract_cells(nr_randuri, nr_coloane):
    """Extrage și salvează toate celulele din tabla de joc"""
    global tabla_x, tabla_y, latime_celula, inaltime_celula
    
    screenshot = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    tabla_logica = []
    
    #os.makedirs("cells", exist_ok=True)
    
    print("[INFO] Extrag celulele...")
    
    for rand in range(nr_randuri):
        linie = []
        for coloana in range(nr_coloane):
            x = tabla_x + coloana * latime_celula
            y = tabla_y + rand * inaltime_celula
            
            celula = img[y:y+inaltime_celula, x:x+latime_celula]
            
            #path = f"cells/cell{rand}_{coloana}.png"
            #cv2.imwrite(path, celula)
            
            label = identifica_celula(celula)
            linie.append(label)
        
        tabla_logica.append(linie)
    
    print(f"[INFO] Am extras {nr_randuri}x{nr_coloane} celule în folderul 'cells/'")
    return tabla_logica

def pune_flags_sigure(tabla_logica):
    global tabla_x, tabla_y, latime_celula, inaltime_celula
    schimbare1 = False
    """Pune steaguri în celulele care sunt cu siguranță bombe"""
    for rand in range(len(tabla_logica)):
        for coloana in range(len(tabla_logica[0])):
            val = tabla_logica[rand][coloana]

            if val.isdigit() and int(val) > 0:
                nr = int(val)

                vecini_necunoscuti = []
                nr_flags = 0

                # sus
                if rand > 0:
                    v = tabla_logica[rand - 1][coloana]
                    if v == "unknow":
                        vecini_necunoscuti.append((rand - 1, coloana))
                    elif v == "flag":
                        nr_flags += 1

                # jos
                if rand < len(tabla_logica) - 1:
                    v = tabla_logica[rand + 1][coloana]
                    if v == "unknow":
                        vecini_necunoscuti.append((rand + 1, coloana))
                    elif v == "flag":
                        nr_flags += 1

                # stanga
                if coloana > 0:
                    v = tabla_logica[rand][coloana - 1]
                    if v == "unknow":
                        vecini_necunoscuti.append((rand, coloana - 1))
                    elif v == "flag":
                        nr_flags += 1

                # dreapta
                if coloana < len(tabla_logica[0]) - 1:
                    v = tabla_logica[rand][coloana + 1]
                    if v == "unknow":
                        vecini_necunoscuti.append((rand, coloana + 1))
                    elif v == "flag":
                        nr_flags += 1

                # sus-stanga
                if rand > 0 and coloana > 0:
                    v = tabla_logica[rand - 1][coloana - 1]
                    if v == "unknow":
                        vecini_necunoscuti.append((rand - 1, coloana - 1))
                    elif v == "flag":
                        nr_flags += 1

                # sus-dreapta
                if rand > 0 and coloana < len(tabla_logica[0]) - 1:
                    v = tabla_logica[rand - 1][coloana + 1]
                    if v == "unknow":
                        vecini_necunoscuti.append((rand - 1, coloana + 1))
                    elif v == "flag":
                        nr_flags += 1

                # jos-stanga
                if rand < len(tabla_logica) - 1 and coloana > 0:
                    v = tabla_logica[rand + 1][coloana - 1]
                    if v == "unknow":
                        vecini_necunoscuti.append((rand + 1, coloana - 1))
                    elif v == "flag":
                        nr_flags += 1

                # jos-dreapta
                if rand < len(tabla_logica) - 1 and coloana < len(tabla_logica[0]) - 1:
                    v = tabla_logica[rand + 1][coloana + 1]
                    if v == "unknow":
                        vecini_necunoscuti.append((rand + 1, coloana + 1))
                    elif v == "flag":
                        nr_flags += 1

                if nr_flags + len(vecini_necunoscuti) == nr:
                    for y, x in vecini_necunoscuti:
                        px = tabla_x + x * latime_celula + latime_celula // 2
                        py = tabla_y + y * inaltime_celula + inaltime_celula // 2

                        screenshot = pyautogui.screenshot()
                        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                        culoare = (0, 0, 255)
                        cv2.imwrite("debug_flag.png", img)

                        pyautogui.rightClick(px, py)
                        schimbare1 = True
                        print(f"[FLAG] Flag la ({y}, {x})")
                        time.sleep(0.05)

                        tabla_logica[y][x] = "flag"
    return schimbare1

def click_stanga_sigur(tabla_logica):
    global tabla_x, tabla_y, latime_celula, inaltime_celula
    schimbare = False
    for rand in range(len(tabla_logica)):
        for coloana in range(len(tabla_logica[0])):
            val = tabla_logica[rand][coloana]

            if val.isdigit() and int(val) > 0:
                nr = int(val)
                nr_flags = 0
                vecini_suspecti = []

                # sus
                if rand > 0:
                    v = tabla_logica[rand - 1][coloana]
                    if v == "flag":
                        nr_flags += 1
                    elif v == "unknow":
                        vecini_suspecti.append((rand - 1, coloana))

                # jos
                if rand < len(tabla_logica) - 1:
                    v = tabla_logica[rand + 1][coloana]
                    if v == "flag":
                        nr_flags += 1
                    elif v == "unknow":
                        vecini_suspecti.append((rand + 1, coloana))

                # stanga
                if coloana > 0:
                    v = tabla_logica[rand][coloana - 1]
                    if v == "flag":
                        nr_flags += 1
                    elif v == "unknow":
                        vecini_suspecti.append((rand, coloana - 1))

                # dreapta
                if coloana < len(tabla_logica[0]) - 1:
                    v = tabla_logica[rand][coloana + 1]
                    if v == "flag":
                        nr_flags += 1
                    elif v == "unknow":
                        vecini_suspecti.append((rand, coloana + 1))

                # sus-stanga
                if rand > 0 and coloana > 0:
                    v = tabla_logica[rand - 1][coloana - 1]
                    if v == "flag":
                        nr_flags += 1
                    elif v == "unknow":
                        vecini_suspecti.append((rand - 1, coloana - 1))

                # sus-dreapta
                if rand > 0 and coloana < len(tabla_logica[0]) - 1:
                    v = tabla_logica[rand - 1][coloana + 1]
                    if v == "flag":
                        nr_flags += 1
                    elif v == "unknow":
                        vecini_suspecti.append((rand - 1, coloana + 1))

                # jos-stanga
                if rand < len(tabla_logica) - 1 and coloana > 0:
                    v = tabla_logica[rand + 1][coloana - 1]
                    if v == "flag":
                        nr_flags += 1
                    elif v == "unknow":
                        vecini_suspecti.append((rand + 1, coloana - 1))

                # jos-dreapta
                if rand < len(tabla_logica) - 1 and coloana < len(tabla_logica[0]) - 1:
                    v = tabla_logica[rand + 1][coloana + 1]
                    if v == "flag":
                        nr_flags += 1
                    elif v == "unknow":
                        vecini_suspecti.append((rand + 1, coloana + 1))

                if nr_flags == nr:
                    for y, x in vecini_suspecti:
                        px = tabla_x + x * latime_celula + latime_celula // 2
                        py = tabla_y + y * inaltime_celula + inaltime_celula // 2

                        pyautogui.click(px, py, button='left')
                        stare = detecteaza_stare_joc()
                        if stare == 'lost':
                            print("Ai pierdut! :(((")
                            sys.exit()
                        elif stare == 'win':
                            print("Ai castigaat!!")
                            sys.exit() 

                        time.sleep(0.05)
                        schimbare = True

                        tabla_logica[y][x] = "empty"#? de ce y x si nu x y?
    return schimbare



def click_random(tabla, tabla_x, tabla_y):
    celule_libere = []

    for y in range(len(tabla)):
        for x in range(len(tabla[0])):
            if tabla[y][x] == 'unknow':
                celule_libere.append((x, y))
    

    x, y = random.choice(celule_libere)

    screen_x = tabla_x + x * latime_celula + latime_celula // 2
    screen_y = tabla_y + y * inaltime_celula + inaltime_celula // 2

    pyautogui.click(screen_x, screen_y)

    stare = detecteaza_stare_joc()
    if stare == 'won':
        print("Ai câștigaaat!!!!")
        sys.exit()
    elif stare == 'lost':
        print("Ai pierdut! :(((")
        sys.exit()

def main(randuri, coloane,tabla_x,tabla_y):
    print("[START] Bot Minesweeper...")
    #click_random(tabla, tabla_x,tabla_y)
    while True:
        tabla = extract_cells(randuri, coloane)
        schimbare1 = pune_flags_sigure(tabla)

        #tabla = extract_cells(randuri, coloane)
        schimbare2 = click_stanga_sigur(tabla)

        if not (schimbare1 or schimbare2):
            stare = detecteaza_stare_joc()
            if stare == 'won':
                print("Ai câștigaaat!!!!")
                sys.exit()
            elif stare == 'playing':
                print("Jocul este încă în desfășurare. Vom alege o pozitie random")
                click_random(tabla, tabla_x,tabla_y)

        time.sleep(0.2)  

    print("[DONE] Tură finalizată.")

if __name__ == "__main__":
    # Detectează tabla o singură dată

    print("Timp pentru a accesa site-ul MineSweeper")
    time.sleep(10)
    
    randuri, coloane, (tabla_x, tabla_y) = gaseste_tabla_info()
    # Actualizează dimensiunile celulelor
    #latime_celula = w
    #inaltime_celula = h
    # Rulează botul
   
    main(randuri, coloane,tabla_x,tabla_y)
