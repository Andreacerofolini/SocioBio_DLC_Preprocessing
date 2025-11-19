import cv2
import os
import sys
import numpy as np
from tqdm import tqdm

# --- IMPORT PATH DAI SETTINGS LOCALI ---
# Aggiunge la cartella superiore per importare config_local.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_local import OUTPUT_CROPPER_PATH 

# --- CONFIGURATION ---
# ORA L'INPUT È L'OUTPUT DEL CROPPER (i video ritagliati)
INPUT_FOLDER = OUTPUT_CROPPER_PATH
OUTPUT_FOLDER = r"output_enhanced"

# Settings per il contrasto (CLAHE)
CLIP_LIMIT = 3.0       # Più alto = più contrasto (prova 2.0 o 3.0)
GRID_SIZE = (8, 8)     # Griglia di suddivisione
# ----------------------

def apply_clahe(image):
    """ Applica il contrasto adattivo (utile per vedere animali scuri su sfondo scuro) """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Applica CLAHE solo sul canale della luminosità (L)
    clahe = cv2.createCLAHE(clipLimit=CLIP_LIMIT, tileGridSize=GRID_SIZE)
    cl = clahe.apply(l)
    
    merged = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Verifica che la cartella di input esista
    if not os.path.exists(INPUT_FOLDER):
        print(f"ERRORE: La cartella di input non esiste: {INPUT_FOLDER}")
        print("Assicurati di aver eseguito lo step precedente (crop_static.py)!")
        return

    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

    if not files:
        print(f"Nessun video trovato in: {INPUT_FOLDER}")
        return

    print(f"Miglioramento contrasto per {len(files)} video...")

    for i, video in enumerate(files):
        path_in = os.path.join(INPUT_FOLDER, video)
        path_out = os.path.join(OUTPUT_FOLDER, f"enh_{video}")
        
        cap = cv2.VideoCapture(path_in)
        
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path_out, fourcc, fps, (w, h))
        
        desc_text = f"Enhance {i+1}/{len(files)}"
        
        with tqdm(total=total_frames, desc=desc_text, unit='fr', ncols=100) as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Applica il filtro di miglioramento
                enhanced_frame = apply_clahe(frame)
                
                out.write(enhanced_frame)
                pbar.update(1)
        
        cap.release()
        out.release()

    print("\n" + "="*60)
    print(" PROCESSO COMPLETATO: Video migliorati in 'output_enhanced'")
    print("="*60)

if __name__ == "__main__":
    main()