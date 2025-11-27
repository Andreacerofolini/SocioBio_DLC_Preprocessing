import cv2
import numpy as np
import os
import pandas as pd
import json
from string import ascii_uppercase
import sys
from tqdm import tqdm 

# Import path dai settings locali
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_local import INPUT_CROPPER_PATH, OUTPUT_CROPPER_PATH, EXCEL_META_PATH 

# --- CONFIGURATION ---
VIDEO_PATH = INPUT_CROPPER_PATH
OUTPUT_PATH = OUTPUT_CROPPER_PATH
EXCEL_PATH = EXCEL_META_PATH
PROGRESS_FILE = "progress_drift.json"

# --- EXPERIMENT SETTINGS ---
NUM_BOXES = 15           
COL_PREFIX = "Pos"       
VIDEO_FPS = 60
SCALE_FACTOR = 1.5       
# ---------------------------

POS_COLUMNS = [f"{COL_PREFIX}{i}" for i in range(1, NUM_BOXES + 1)]

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
    state = param['state']
    real_x = int(x / SCALE_FACTOR)
    real_y = int(y / SCALE_FACTOR)

    if state['mode'] == 'DRAW_BOX':
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

    elif state['mode'] == 'DRIFT_POINT':
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(state['drift_points']) < 2:
                state['drift_points'].append((real_x, real_y))
                print(f"Drift Point Added: {real_x}, {real_y}")

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
    print("ERRORE COLONNA: Non trovo la colonna 'Original_Name' nel CSV.")
    return None

def main():
    if not os.path.exists(OUTPUT_PATH): os.makedirs(OUTPUT_PATH)
    files = get_video_files(VIDEO_PATH)
    processed_files = load_progress()
    df = load_csv_smart(EXCEL_PATH)
    if df is None: return 

    # Coda dei lavori da processare dopo il setup
    jobs_queue = []

    # --- LEGENDA TASTI SUL TERMINALE ---
    print("\n" + "=" * 60)
    print(f" DRIFT CORRECTION MODE | Subjects: {NUM_BOXES}")
    print("=" * 60)
    print("  MODALITÀ BATCH: Configura tutto ora, processa dopo.")
    print("-" * 60)
    print("  [Click] : Draw Box (2 clicks) OR Place Drift Point")
    print("  [ n ]   : Confirm Box")
    print("  [ z ]   : Undo (Last Box or Last Point)")
    print("-" * 60)
    print("  [ d ]   : DRIFT TOOL (Click Start -> 'e' -> Click End)")
    print("  [ e ]   : GO TO END (Check drift)")
    print("  [ r ]   : RESET VIEW (Go to start)")
    print("-" * 60)
    print("  [ s ]   : SAVE CONFIG & NEXT VIDEO (No processing yet)")
    print("  [ Esc ] : Exit Setup & Start Processing Queued Jobs")
    print("=" * 60 + "\n")
    # -----------------------------------

    # --- FASE 1: SETUP UTENTE (Tutti i video) ---
    for video_file in files:
        if video_file in processed_files: continue

        search_name = video_file.replace("proc_", "").replace(".mp4", "").replace(".mov", "")
        search_name = os.path.splitext(search_name)[0]

        if search_name not in df['Original_Name'].values:
            print(f"SKIP: {video_file} (Non trovato nel CSV)")
            continue

        row = df[df['Original_Name'] == search_name].iloc[0]
        subjects = [str(row[col]) for col in POS_COLUMNS]

        cap = cv2.VideoCapture(os.path.join(VIDEO_PATH, video_file))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        state = {
            'mode': 'DRAW_BOX', 'drawing': False, 'start_point': (0,0), 'current_end': (0,0), 
            'temp_box': None, 'boxes': [], 'drift_points': [], 'frame_idx': 0
        }
        drift_calculated = False
        total_drift = (0, 0)

        win_name = f"Setup ({len(jobs_queue)+1}): {video_file}"
        cv2.namedWindow(win_name)
        cv2.setMouseCallback(win_name, mouse_callback, {'state': state})
        
        setup_completed = False

        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, state['frame_idx'])
            ret, frame = cap.read()
            if not ret: break

            h, w = frame.shape[:2]
            disp_w, disp_h = int(w * SCALE_FACTOR), int(h * SCALE_FACTOR)
            display_frame = cv2.resize(frame, (disp_w, disp_h))

            # --- CALCOLO DRIFT ---
            if len(state['drift_points']) == 2:
                p1, p2 = state['drift_points']
                total_drift = (p2[0] - p1[0], p2[1] - p1[1])
                drift_calculated = True
            else:
                drift_calculated = False
                total_drift = (0, 0)

            # --- CALCOLO SPOSTAMENTO CORRENTE (LIVE PREVIEW) ---
            current_shift_x, current_shift_y = 0, 0
            if drift_calculated and total_frames > 0:
                progress = state['frame_idx'] / total_frames
                current_shift_x = int(total_drift[0] * progress)
                current_shift_y = int(total_drift[1] * progress)

            # 1. Disegna i box (DINAMICI)
            for i, box in enumerate(state['boxes']):
                bx1, by1, bx2, by2 = box
                curr_x1 = bx1 + current_shift_x
                curr_y1 = by1 + current_shift_y
                curr_x2 = bx2 + current_shift_x
                curr_y2 = by2 + current_shift_y
                dx1, dy1, dx2, dy2 = [int(c * SCALE_FACTOR) for c in [curr_x1, curr_y1, curr_x2, curr_y2]]
                
                label_text = subjects[i] if i < len(subjects) else f"Box {i}"
                cv2.rectangle(display_frame, (dx1, dy1), (dx2, dy2), COLORS[i % len(COLORS)], 2)
                cv2.putText(display_frame, label_text, (dx1, dy1 - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLORS[i % len(COLORS)], 2)

            # 2. Disegna box in costruzione
            if state['drawing']:
                sx, sy = state['start_point']
                ex, ey = state['current_end']
                d_sx, d_sy = int(sx * SCALE_FACTOR), int(sy * SCALE_FACTOR)
                d_ex, d_ey = int(ex * SCALE_FACTOR), int(ey * SCALE_FACTOR)
                cv2.rectangle(display_frame, (d_sx, d_sy), (d_ex, d_ey), (0, 255, 255), 1)

            # 3. Box temporaneo
            if state['temp_box']:
                bx1, by1, bx2, by2 = [int(c * SCALE_FACTOR) for c in state['temp_box']]
                next_idx = len(state['boxes'])
                preview_label = subjects[next_idx] if next_idx < len(subjects) else "..."
                cv2.rectangle(display_frame, (bx1, by1), (bx2, by2), (0, 255, 255), 2)
                cv2.putText(display_frame, f"Next: {preview_label}", (bx1, by1 - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # 4. Visualizzazione Drift
            if len(state['drift_points']) > 0:
                p1 = state['drift_points'][0]
                cv2.circle(display_frame, (int(p1[0]*SCALE_FACTOR), int(p1[1]*SCALE_FACTOR)), 5, (0, 0, 255), -1)
                if len(state['drift_points']) > 1:
                    p2 = state['drift_points'][1]
                    cv2.circle(display_frame, (int(p2[0]*SCALE_FACTOR), int(p2[1]*SCALE_FACTOR)), 5, (0, 0, 255), -1)
                    cv2.line(display_frame, (int(p1[0]*SCALE_FACTOR), int(p1[1]*SCALE_FACTOR)), 
                                            (int(p2[0]*SCALE_FACTOR), int(p2[1]*SCALE_FACTOR)), (0, 255, 0), 2)

            # Info testo
            info_txt = f"File: {video_file} | Box: {len(state['boxes'])}/{NUM_BOXES}"
            if drift_calculated: 
                info_txt += f" | Drift: OK"
            
            cv2.putText(display_frame, info_txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow(win_name, display_frame)
            
            key = cv2.waitKey(1) & 0xFF

            if key == ord('n'): 
                if state['temp_box']:
                    state['boxes'].append(state['temp_box'])
                    state['temp_box'] = None
            elif key == ord('z'): 
                if state['mode'] == 'DRIFT_POINT' and state['drift_points']: 
                    state['drift_points'].pop()
                elif state['boxes']: 
                    state['boxes'].pop()

            elif key == ord('e'): state['frame_idx'] = total_frames - 100 if total_frames > 100 else 0
            elif key == ord('r'): state['frame_idx'] = 0
            elif key == ord('d'): state['mode'] = 'DRIFT_POINT'
            elif key == ord('s'): 
                if len(state['boxes']) == NUM_BOXES:
                    # SALVA IL LAVORO IN CODA
                    job_data = {
                        'file': video_file,
                        'boxes': state['boxes'],
                        'drift': total_drift,
                        'subjects': subjects,
                        'drift_calculated': drift_calculated
                    }
                    jobs_queue.append(job_data)
                    print(f" -> Configurazione salvata per: {video_file}")
                    setup_completed = True
                    break
                else: print(f"Define all {NUM_BOXES} boxes first!")
            elif key == 27: # ESC
                print("Setup interrotto dall'utente. Avvio processamento dei video già configurati...")
                break
        
        cap.release()
        cv2.destroyWindow(win_name)
        if not setup_completed and key == 27:
            break

    # --- FASE 2: BATCH PROCESSING ---
    if not jobs_queue:
        print("Nessun video configurato. Esco.")
        return

    print("\n" + "=" * 60)
    print(f" AVVIO ELABORAZIONE BATCH: {len(jobs_queue)} video in coda")
    print("=" * 60)

    for job in jobs_queue:
        video_file = job['file']
        boxes = job['boxes']
        total_drift = job['drift']
        subjects = job['subjects']
        drift_calculated = job['drift_calculated']

        cap = cv2.VideoCapture(os.path.join(VIDEO_PATH, video_file))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Preparazione Writers
        writers = []
        clean_name_for_output = os.path.splitext(video_file)[0] 
        
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            w_box, h_box = x2 - x1, y2 - y1
            sub_name = subjects[i]
            out_name = f"{sub_name}_{clean_name_for_output}.mp4"
            out_full = os.path.join(OUTPUT_PATH, out_name)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writers.append({'writer': cv2.VideoWriter(out_full, fourcc, VIDEO_FPS, (w_box, h_box)), 'base_coords': (x1, y1), 'w': w_box, 'h': h_box})

        # Loop di scrittura
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        with tqdm(total=total_frames, desc=f"Processing {video_file}", unit='frame', leave=True) as pbar:
            while True:
                ret, frame = cap.read()
                if not ret: break
                frame_idx = cap.get(cv2.CAP_PROP_POS_FRAMES)
                
                shift_x, shift_y = 0, 0
                if drift_calculated and total_frames > 0:
                    progress = frame_idx / total_frames
                    shift_x = int(total_drift[0] * progress)
                    shift_y = int(total_drift[1] * progress)
                
                img_h, img_w = frame.shape[:2]
                for item in writers:
                    base = item['base_coords']
                    # Calcolo coordinate con drift
                    curr_x1 = max(0, min(base[0] + shift_x, img_w - 1))
                    curr_y1 = max(0, min(base[1] + shift_y, img_h - 1))
                    curr_x2 = max(curr_x1 + 1, min(curr_x1 + item['w'], img_w))
                    curr_y2 = max(curr_y1 + 1, min(curr_y1 + item['h'], img_h))
                    
                    crop = frame[curr_y1:curr_y2, curr_x1:curr_x2]
                    
                    # Sicurezza dimensioni
                    if crop.shape[0] != item['h'] or crop.shape[1] != item['w']:
                        crop = cv2.resize(crop, (item['w'], item['h']))
                    
                    item['writer'].write(crop)
                pbar.update(1)

        for item in writers: item['writer'].release()
        cap.release()
        
        # Aggiorna file di progresso dopo ogni video completato
        processed_files[video_file] = True
        save_progress(processed_files)
        print(f"Completato: {video_file}")

    print("\n" + "=" * 60)
    print(" TUTTI I JOB COMPLETATI!")
    print("=" * 60)

if __name__ == "__main__":
    main()