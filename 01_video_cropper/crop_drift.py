import cv2
import numpy as np
import os
import pandas as pd
import json
from string import ascii_uppercase
import sys

# --- CONFIGURATION ---
VIDEO_PATH = r"C:\Path\To\RawVideos"
OUTPUT_PATH = r"C:\Path\To\CroppedVideos"
EXCEL_PATH = r"C:\Path\To\Data\metadata.xlsx"
PROGRESS_FILE = "progress_drift.json"

NUM_BOXES = 15 
VIDEO_FPS = 60
SCALE_FACTOR = 0.5 

COL_FILENAME = "file name" 
POS_COLUMNS = [f"Pos{i}" for i in range(1, 16)] 
# --- END CONFIGURATION ---

BOX_NAMES = list(ascii_uppercase)[:NUM_BOXES]
np.random.seed(42)
BOX_COLORS = [tuple(map(int, np.random.randint(50, 255, 3))) for _ in range(NUM_BOXES)]
current_coords = []

def get_coordinate(event, x, y, flags, param):
    global current_coords
    if event == cv2.EVENT_LBUTTONDOWN:
        real_x = int(x / SCALE_FACTOR)
        real_y = int(y / SCALE_FACTOR)
        current_coords.append((real_x, real_y))

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(data):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_metadata():
    if not os.path.exists(EXCEL_PATH):
        print(f"ERROR: Excel file not found: {EXCEL_PATH}")
        sys.exit()
    try:
        if EXCEL_PATH.endswith('.csv'):
            df = pd.read_csv(EXCEL_PATH)
        else:
            df = pd.read_excel(EXCEL_PATH)
        df.columns = [str(c).strip() for c in df.columns]
        if COL_FILENAME in df.columns:
            df[COL_FILENAME] = df[COL_FILENAME].astype(str).str.strip()
        return df
    except Exception as e:
        print(f"Error reading metadata: {e}")
        sys.exit()

def main():
    global current_coords
    if not os.path.exists(OUTPUT_PATH): os.makedirs(OUTPUT_PATH)

    df_info = load_metadata()
    video_files = [f for f in os.listdir(VIDEO_PATH) if f.lower().endswith(('.mov', '.mp4', '.avi'))]
    completed_work = load_progress()
    last_cuts_memory = None 

    print("-" * 50)
    print("DRIFT CORRECTION MODE - COMMANDS:")
    print("  [Left Click]: Draw box / Define drift points")
    print("  [ n ]       : Confirm Box")
    print("  [ z ]       : Undo")
    print("  [ c ]       : Copy from previous video")
    print("  [ e ]       : GOTO END (Check for movement)")
    print("  [ r ]       : RESET VIEW (Back to start)")
    print("  [ d ]       : CALCULATE DRIFT (If camera moved)")
    print("  [ s ]       : SAVE and PROCESS")
    print("-" * 50)

    for video_file in video_files:
        if video_file in completed_work: continue

        video_name_clean = os.path.splitext(video_file)[0]
        row = df_info[df_info[COL_FILENAME] == video_name_clean]
        if row.empty:
            row = df_info[df_info[COL_FILENAME].str.contains(video_name_clean, regex=False)]
        
        if row.empty:
            print(f"SKIP: {video_file} not in Excel.")
            continue
        
        try:
            subjects = []
            for col in POS_COLUMNS:
                val = str(row.iloc[0][col]).strip()
                val = "".join(c for c in val if c.isalnum() or c in "_-")
                subjects.append(val)
        except: continue

        print(f"\n>>> PROCESSING: {video_file}")
        
        video_path = os.path.join(VIDEO_PATH, video_file)
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if not cap.isOpened(): continue
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame_start = cap.read()
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 5)
        ret2, frame_end = cap.read()
        
        if not ret or not ret2: continue

        current_frame = frame_start.copy()
        viewing_end = False 
        
        cv2.namedWindow('Cutter', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('Cutter', get_coordinate)

        cuts = {} 
        drift_vector = (0, 0) 
        current_idx = 0 
        current_coords = []
        drift_mode = False 

        while True:
            display = cv2.resize(current_frame, (0,0), fx=SCALE_FACTOR, fy=SCALE_FACTOR)
            
            if drift_vector != (0,0):
                cv2.putText(display, f"DRIFT ACTIVE: X={drift_vector[0]} Y={drift_vector[1]}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            for i, (k, v) in enumerate(cuts.items()):
                x1, y1, x2, y2 = v
                if viewing_end:
                    x1 += drift_vector[0]
                    x2 += drift_vector[0]
                    y1 += drift_vector[1]
                    y2 += drift_vector[1]

                p1 = (int(x1*SCALE_FACTOR), int(y1*SCALE_FACTOR))
                p2 = (int(x2*SCALE_FACTOR), int(y2*SCALE_FACTOR))
                col = BOX_COLORS[i]
                cv2.rectangle(display, p1, p2, col, 2)
                
                if viewing_end and drift_vector == (0,0):
                     orig_p1 = (int(v[0]*SCALE_FACTOR), int(v[1]*SCALE_FACTOR))
                     orig_p2 = (int(v[2]*SCALE_FACTOR), int(v[3]*SCALE_FACTOR))
                     cv2.rectangle(display, orig_p1, orig_p2, (100,100,100), 1)

            if drift_mode:
                cv2.putText(display, "DRIFT MODE: Click START point, then END point", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            elif not viewing_end and current_idx < NUM_BOXES:
                msg = f"Draw {BOX_NAMES[current_idx]}: {subjects[current_idx]}"
                cv2.putText(display, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            elif viewing_end:
                cv2.putText(display, "END VIEW. Press 'd' to fix drift.", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

            if len(current_coords) > 0:
                 pt = (int(current_coords[-1][0]*SCALE_FACTOR), int(current_coords[-1][1]*SCALE_FACTOR))
                 cv2.circle(display, pt, 5, (0,0,255), -1)
                 if len(current_coords) == 2 and not drift_mode:
                    p1 = (int(current_coords[0][0]*SCALE_FACTOR), int(current_coords[0][1]*SCALE_FACTOR))
                    p2 = (int(current_coords[1][0]*SCALE_FACTOR), int(current_coords[1][1]*SCALE_FACTOR))
                    cv2.rectangle(display, p1, p2, BOX_COLORS[current_idx], 2)

            cv2.imshow('Cutter', display)
            key = cv2.waitKey(20) & 0xFF

            if key == ord('n') and not drift_mode and not viewing_end:
                if len(current_coords) == 2:
                    c = current_coords
                    cuts[BOX_NAMES[current_idx]] = [min(c[0][0], c[1][0]), min(c[0][1], c[1][1]), max(c[0][0], c[1][0]), max(c[0][1], c[1][1])]
                    current_idx += 1
                    current_coords = []

            elif key == ord('e'):
                viewing_end = True
                current_frame = frame_end.copy()
                current_coords = [] 

            elif key == ord('r'):
                viewing_end = False
                drift_mode = False
                current_frame = frame_start.copy()
                current_coords = []

            elif key == ord('d'):
                print("Drift tool activated...")
                viewing_end = False 
                current_frame = frame_start.copy()
                drift_mode = True
                current_coords = [] 
                drift_vector = (0,0) 

            if drift_mode and len(current_coords) == 1 and not viewing_end:
                viewing_end = True
                current_frame = frame_end.copy()
                
            if drift_mode and len(current_coords) == 2 and viewing_end:
                p_start = current_coords[0]
                p_end = current_coords[1]
                dx = p_end[0] - p_start[0]
                dy = p_end[1] - p_start[1]
                drift_vector = (dx, dy)
                print(f"Drift Calculated: X={dx}, Y={dy}")
                drift_mode = False
                current_coords = []

            elif key == ord('c') and not viewing_end:
                if last_cuts_memory:
                    cuts = last_cuts_memory['cuts'].copy()
                    drift_vector = last_cuts_memory['drift'] 
                    current_idx = NUM_BOXES
                else: print("Nothing to copy.")

            elif key == ord('z'):
                if current_coords: current_coords.pop()
                elif current_idx > 0 and not drift_mode:
                    current_idx -= 1
                    del cuts[BOX_NAMES[current_idx]]

            elif key == ord('s'):
                if len(cuts) == NUM_BOXES:
                    cv2.destroyWindow('Cutter')
                    process_video(video_file, video_path, cuts, subjects, drift_vector)
                    completed_work[video_file] = cuts
                    save_progress(completed_work)
                    last_cuts_memory = {'cuts': cuts, 'drift': drift_vector}
                    break

            elif key == 27:
                cap.release()
                cv2.destroyAllWindows()
                return
        cap.release()

def process_video(filename, filepath, cuts_dict, subjects_list, total_drift):
    cap = cv2.VideoCapture(filepath)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    writers = []
    
    clean_name = os.path.splitext(filename)[0]
    
    for i, (key, coords) in enumerate(cuts_dict.items()):
        subject = subjects_list[i]
        w = coords[2] - coords[0]
        h = coords[3] - coords[1]
        out_name = f"{subject}_{clean_name}.mp4"
        out_full = os.path.join(OUTPUT_PATH, out_name)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writers.append({
            'writer': cv2.VideoWriter(out_full, fourcc, VIDEO_FPS, (w, h)),
            'base_coords': coords, 
            'w': w, 'h': h
        })

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        if total_drift != (0,0) and total_frames > 0:
            shift_x = int(total_drift[0] * (frame_idx / total_frames))
            shift_y = int(total_drift[1] * (frame_idx / total_frames))
        else:
            shift_x, shift_y = 0, 0

        img_h, img_w = frame.shape[:2]

        for item in writers:
            base = item['base_coords']
            curr_x1 = base[0] + shift_x
            curr_y1 = base[1] + shift_y
            curr_x2 = curr_x1 + item['w']
            curr_y2 = curr_y1 + item['h']

            curr_x1 = max(0, min(curr_x1, img_w - 1))
            curr_y1 = max(0, min(curr_y1, img_h - 1))
            curr_x2 = max(curr_x1 + 1, min(curr_x2, img_w))
            curr_y2 = max(curr_y1 + 1, min(curr_y2, img_h))
            
            crop = frame[curr_y1:curr_y2, curr_x1:curr_x2]
            
            if crop.shape[0] != item['h'] or crop.shape[1] != item['w']:
                 crop = cv2.resize(crop, (item['w'], item['h']))

            item['writer'].write(crop)
        frame_idx += 1

    cap.release()
    for item in writers: item['writer'].release()
    print(f"Finished: {filename}")

if __name__ == "__main__":
    main()