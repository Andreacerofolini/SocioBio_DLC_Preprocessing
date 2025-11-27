import cv2
import numpy as np
import os
import pandas as pd
import json
from string import ascii_uppercase
import sys
from tqdm import tqdm 

# Import path locali
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_local import INPUT_CROPPER_PATH, OUTPUT_CROPPER_PATH, EXCEL_META_PATH

# --- CONFIGURATION ---
VIDEO_PATH = INPUT_CROPPER_PATH
OUTPUT_PATH = OUTPUT_CROPPER_PATH
EXCEL_PATH = EXCEL_META_PATH
PROGRESS_FILE = "progress_static.json"

# --- EXPERIMENT SETTINGS ---
NUM_BOXES = 15           
COL_PREFIX = "Pos"       
VIDEO_FPS = 60           
SCALE_FACTOR = 1.5       
# ---------------------------

POS_COLUMNS = [f"{COL_PREFIX}{i}" for i in range(1, NUM_BOXES + 1)]

# Generiamo colori random per i box
np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(NUM_BOXES, 3), dtype=np.uint8).tolist()

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(data):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_video_files(folder):
    return [f for f in os.listdir(folder) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

def mouse_callback(event, x, y, flags, param):
    """ MODALITÀ DUE CLICK """
    state = param['state']
    real_x = int(x / SCALE_FACTOR)
    real_y = int(y / SCALE_FACTOR)

    if event == cv2.EVENT_LBUTTONDOWN:
        if not state['drawing']:
            state['drawing'] = True
            state['start_point'] = (real_x, real_y)
            state['current_end'] = (real_x, real_y)
        else:
            state['drawing'] = False
            x1, y1 = state['start_point']
            x2, y2 = (real_x, real_y)
            state['temp_box'] = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    elif event == cv2.EVENT_MOUSEMOVE:
        state['current_end'] = (real_x, real_y)

def load_csv_smart(path):
    separators = [',', ';', '\t']
    if not os.path.exists(path):
        print(f"ERRORE: File CSV non trovato: {path}")
        return None

    for sep in separators:
        try:
            df = pd.read_csv(path, sep=sep)
            if 'Original_Name' in df.columns:
                print(f"CSV caricato con successo (separatore: '{sep}')")
                df['Original_Name'] = df['Original_Name'].astype(str).str.strip()
                df['Original_Name'] = df['Original_Name'].apply(lambda x: os.path.splitext(x)[0])
                return df
        except:
            continue
    print("ERRORE CRITICO: Non trovo la colonna 'Original_Name' nel CSV.")
    return None

def main():
    if not os.path.exists(OUTPUT_PATH): os.makedirs(OUTPUT_PATH)
    df = load_csv_smart(EXCEL_PATH)
    if df is None: return
    files = get_video_files(VIDEO_PATH)
    processed_files = load_progress()

    jobs_queue = []
    last_cuts_memory = None  # Per la funzione 'c' (copia precedente)

    print("\n" + "=" * 60)
    print(f" STATIC CROP MODE | Subjects: {NUM_BOXES}")
    print("=" * 60)
    print("  MODALITÀ BATCH: Configura tutto ora, processa dopo.")
    print("-" * 60)
    print("  [Click] : Start/End Box")
    print("  [ n ]   : Confirm Box")
    print("  [ z ]   : Undo")
    print("  [ c ]   : Copy Previous Boxes (from previous video)")
    print("-" * 60)
    print("  [ s ]   : SAVE CONFIG & NEXT VIDEO")
    print("  [ Esc ] : Exit Setup & Start Processing")
    print("=" * 60 + "\n")

    # --- FASE 1: SETUP UTENTE ---
    for i, video_file in enumerate(files):
        if video_file in processed_files:
            continue

        search_name = video_file.replace("proc_", "").replace(".mp4", "").replace(".mov", "").replace(".avi", "")
        search_name = os.path.splitext(search_name)[0]

        if search_name not in df['Original_Name'].values:
            print(f"SKIP: {video_file} (Not found in CSV)")
            continue

        # Dati dal CSV
        row = df[df['Original_Name'] == search_name].iloc[0]
        current_subjects = [str(row[col]) for col in POS_COLUMNS]

        cap = cv2.VideoCapture(os.path.join(VIDEO_PATH, video_file))
        if not cap.isOpened(): continue
        
        ret, frame = cap.read()
        cap.release() # Chiudiamo subito, riapriremo dopo
        if not ret: continue
        
        state = {'drawing': False, 'start_point': (0,0), 'current_end': (0,0), 'temp_box': None, 'boxes': []}
        
        win_name = f"Setup ({len(jobs_queue)+1}): {video_file}"
        cv2.namedWindow(win_name)
        cv2.setMouseCallback(win_name, mouse_callback, {'state': state})
        
        setup_completed = False

        while True:
            h, w = frame.shape[:2]
            disp_w, disp_h = int(w * SCALE_FACTOR), int(h * SCALE_FACTOR)
            display_frame = cv2.resize(frame, (disp_w, disp_h))

            # Disegna i box confermati
            for idx, box in enumerate(state['boxes']):
                bx1, by1, bx2, by2 = [int(c * SCALE_FACTOR) for c in box]
                color = COLORS[idx % len(COLORS)]
                label_text = current_subjects[idx] if idx < len(current_subjects) else f"Box {idx+1}"
                cv2.rectangle(display_frame, (bx1, by1), (bx2, by2), color, 2)
                cv2.putText(display_frame, label_text, (bx1, by1 - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Box in costruzione
            if state['drawing']:
                sx, sy = state['start_point']
                ex, ey = state['current_end']
                d_sx, d_sy = int(sx * SCALE_FACTOR), int(sy * SCALE_FACTOR)
                d_ex, d_ey = int(ex * SCALE_FACTOR), int(ey * SCALE_FACTOR)
                cv2.rectangle(display_frame, (d_sx, d_sy), (d_ex, d_ey), (0, 255, 255), 1)

            # Box temporaneo
            if state['temp_box']:
                bx1, by1, bx2, by2 = [int(c * SCALE_FACTOR) for c in state['temp_box']]
                next_idx = len(state['boxes'])
                preview_label = current_subjects[next_idx] if next_idx < len(current_subjects) else "..."
                cv2.rectangle(display_frame, (bx1, by1), (bx2, by2), (0, 255, 255), 2)
                cv2.putText(display_frame, f"Next: {preview_label}", (bx1, by1 - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            info_txt = f"File: {video_file} | Box: {len(state['boxes'])}/{NUM_BOXES}"
            cv2.putText(display_frame, info_txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow(win_name, display_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('n'): 
                if state['temp_box']:
                    state['boxes'].append(state['temp_box'])
                    state['temp_box'] = None
            elif key == ord('z'): 
                if state['boxes']: state['boxes'].pop()
            elif key == ord('c'): 
                if last_cuts_memory: 
                    # Copia profonda per evitare riferimenti incrociati
                    state['boxes'] = list(last_cuts_memory)
                    print("Copiati box dal video precedente.")
                else:
                    print("Nessun box precedente in memoria.")
            elif key == ord('s'): 
                if len(state['boxes']) == NUM_BOXES:
                    # SALVA NEL JOB QUEUE
                    jobs_queue.append({
                        'filename': video_file,
                        'filepath': os.path.join(VIDEO_PATH, video_file),
                        'boxes': state['boxes'],
                        'subjects': current_subjects
                    })
                    last_cuts_memory = state['boxes'] # Memorizza per il prossimo 'c'
                    setup_completed = True
                    break
                else:
                    print(f"Definisci esattamente {NUM_BOXES} box.")
            elif key == 27: # ESC
                print("Setup interrotto dall'utente. Avvio processamento...")
                break

        cv2.destroyWindow(win_name)
        if not setup_completed and key == 27:
            break

    # --- FASE 2: BATCH PROCESSING ---
    if not jobs_queue:
        print("Nessun video da processare.")
        return

    print("\n" + "=" * 60)
    print(f" AVVIO ELABORAZIONE BATCH: {len(jobs_queue)} video in coda")
    print("=" * 60)

    for job in jobs_queue:
        filename = job['filename']
        filepath = job['filepath']
        boxes = job['boxes']
        subjects_list = job['subjects']

        cap = cv2.VideoCapture(filepath)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        writers = []
        clean_name = os.path.splitext(filename.replace("proc_", ""))[0]
        
        # Setup writers
        for i, coords in enumerate(boxes):
            subject = subjects_list[i]
            x1, y1, x2, y2 = coords
            w, h = x2 - x1, y2 - y1
            out_name = f"{subject}_{clean_name}.mp4"
            out_full = os.path.join(OUTPUT_PATH, out_name)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writers.append({'writer': cv2.VideoWriter(out_full, fourcc, VIDEO_FPS, (w, h)), 'coords': coords})

        # Processing loop
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        with tqdm(total=total_frames, desc=f"Writing {filename}", unit='frame', leave=True) as pbar:
            while True:
                ret, frame = cap.read()
                if not ret: break
                
                # Scrittura dei crop
                for item in writers:
                    x1, y1, x2, y2 = item['coords']
                    crop = frame[y1:y2, x1:x2]
                    item['writer'].write(crop)
                pbar.update(1)
                
        for item in writers: item['writer'].release()
        cap.release()
        
        processed_files[filename] = True
        save_progress(processed_files)
        print(f"Completato: {filename}")

    print("\n" + "=" * 60)
    print(" TUTTI I JOB COMPLETATI!")
    print("=" * 60)

if __name__ == "__main__":
    main()