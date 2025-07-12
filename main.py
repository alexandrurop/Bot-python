import time
import pyautogui
import cv2
import numpy as np
import os

# Configurări tabla
tabla_x = 104
tabla_y = 311
latime_celula = 24
inaltime_celula = 24
nr_randuri = 16
nr_coloane = 30

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

def extract_cells():
    """Extrage și salvează toate celulele din tabla de joc"""
    screenshot = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    tabla_logica = []
    
    # Creează folderul dacă nu există
    os.makedirs("cells", exist_ok=True)
    
    print("[INFO] Extrag celulele...")
    
    for rand in range(nr_randuri):
        linie = []
        for coloana in range(nr_coloane):
            x = tabla_x + coloana * latime_celula
            y = tabla_y + rand * inaltime_celula
            
            celula = img[y:y+inaltime_celula, x:x+latime_celula]
            
            # Salvează fiecare celulă individual
            path = f"cells/cell{rand}_{coloana}.png"
            cv2.imwrite(path, celula)
            
            label = identifica_celula(celula)
            linie.append(label)
        
        tabla_logica.append(linie)
    
    print(f"[INFO] Am extras {nr_randuri}x{nr_coloane} celule în folderul 'celule/'")
    return tabla_logica

def pune_flags_sigure(tabla_logica):
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

                # Dacă numărul de necunoscute + flaguri existente == număr din celulă
                if nr_flags + len(vecini_necunoscuti) == nr:
                    for y, x in vecini_necunoscuti:
                        # Click dreapta pe celula (y, x)
                        px = tabla_x + x * latime_celula + latime_celula // 2
                        py = tabla_y + y * inaltime_celula + inaltime_celula // 2

                        # Debug vizual (opțional)
                        screenshot = pyautogui.screenshot()
                        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                        culoare = (0, 0, 255)
                        cv2.circle(img, (px, py), radius=5, color=culoare, thickness=-1)
                        cv2.imwrite("debug_flag.png", img)

                        pyautogui.rightClick(px, py)
                        print(f"[FLAG] Flag la ({y}, {x})")
                        time.sleep(0.05)

                        # Marchez în tabla logică ca "flag"
                        tabla_logica[y][x] = "flag"

def afiseaza_matrice(tabla_logica):
    """Afișează tabla ca o matrice frumoasă"""
    print("\n" + "="*60)
    print("TABLA MINESWEEPER")
    print("="*60)
    
    # Header cu numerele coloanelor
    print("   ", end="")
    for col in range(nr_coloane):
        print(f"{col:>8}", end="")
    print()
    
    # Fiecare rând
    for rand in range(nr_randuri):
        print(f"{rand:2}: ", end="")
        for coloana in range(nr_coloane):
            celula = tabla_logica[rand][coloana]
            if celula == "necunoscut":
                print(f"{'?':>8}", end="")
            elif celula == "flag":
                print(f"{'flag':>8}", end="")
            else:
                print(f"{celula:>8}", end="")
        print()
    print("="*60)
                
def main():
    print("[START] Bot Minesweeper...")
    tabla = extract_cells()
    pune_flags_sigure(tabla)
    #click_stanga_sigur(tabla)
    #afiseaza_matrice(tabla)
    print("[DONE] Tură finalizată.")


if __name__ == "__main__":
    main()