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
EXCEL_PATH = r"C:\Path\To\Data\metadata.xlsx" # or .csv
PROGRESS_FILE = "progress_static.json"

# Video Settings
NUM_BOXES = 15  # Exact number of subjects
VIDEO_FPS = 60
SCALE_FACTOR = 0.5 # Zoom factor for the display window

# EXCEL COLUMN NAMES
COL_FILENAME = "file name" 
# List of columns containing subject names (Position 1 to 15)
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
        print(f"ERROR: Excel file not found at: {EXCEL_PATH}")
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

    print("--- START ---")
    print(f"Reading Metadata: {EXCEL_PATH}")
    df_info = load_metadata()
    
    all_files = os.listdir(VIDEO_PATH)
    video_files = [f for f in all_files if f.lower().endswith(('.mov', '.mp4', '.avi'))]
    
    completed_work = load_progress()
    last_cuts_memory = None 

    print(f"Found {len(video_files)} videos. {len(completed_work)} already processed.")
    print("\nKEYBOARD COMMANDS:")
    print("  [Left Click]: Define box corners")
    print("  [ n ]       : NEXT (Confirm box)")
    print("  [ z ]       : UNDO (Last click/box)")
    print("  [ c ]       : COPY boxes from previous video")
    print("  [ s ]       : SAVE and process")
    print("  [ ESC ]     : Exit")
    print("-" * 40)

    for video_file in video_files:
        if video_file in completed_work: continue

        video_name_clean = os.path.splitext(video_file)[0]
        row = df_info[df_info[COL_FILENAME] == video_name_clean]
        
        if row.empty:
            # Try partial match
            row = df_info[df_info[COL_FILENAME].str.contains(video_name_clean, regex=False)]

        if row.empty:
            print(f"\n[SKIP] Video '{video_file}' not found in Excel.")
            continue
        
        try:
            subjects = []
            for col in POS_COLUMNS:
                val = str(row.iloc[0][col]).strip()
                val = "".join(c for c in val if c.isalnum() or c in "_-")
                subjects.append(val)
        except Exception as e:
            print(f"Error parsing subjects: {e}")
            continue

        print(f"\n>>> PROCESSING: {video_file}")
        
        cap = cv2.VideoCapture(os.path.join(VIDEO_PATH, video_file))
        if not cap.isOpened(): continue
        ret, frame = cap.read()
        if not ret: continue

        cv2.namedWindow('Cutter', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('Cutter', get_coordinate)

        cuts = {} 
        current_idx = 0 
        current_coords = []

        while True:
            display = cv2.resize(frame, (0,0), fx=SCALE_FACTOR, fy=SCALE_FACTOR)
            
            for i, (k, v) in enumerate(cuts.items()):
                p1 = (int(v[0]*SCALE_FACTOR), int(v[1]*SCALE_FACTOR))
                p2 = (int(v[2]*SCALE_FACTOR), int(v[3]*SCALE_FACTOR))
                col = BOX_COLORS[i]
                cv2.rectangle(display, p1, p2, col, 2)
                cv2.putText(display, f"{k}:{subjects[i]}", (p1[0], p1[1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2)

            if current_idx < NUM_BOXES:
                curr_col = BOX_COLORS[current_idx]
                msg = f"Draw {BOX_NAMES[current_idx]} for: {subjects[current_idx]}"
                cv2.putText(display, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                if len(current_coords) == 1:
                    pt = (int(current_coords[0][0]*SCALE_FACTOR), int(current_coords[0][1]*SCALE_FACTOR))
                    cv2.circle(display, pt, 5, curr_col, -1)
                elif len(current_coords) == 2:
                    p1 = (int(current_coords[0][0]*SCALE_FACTOR), int(current_coords[0][1]*SCALE_FACTOR))
                    p2 = (int(current_coords[1][0]*SCALE_FACTOR), int(current_coords[1][1]*SCALE_FACTOR))
                    cv2.rectangle(display, p1, p2, curr_col, 2)
            else:
                cv2.putText(display, "DONE! Press 's' to save.", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.imshow('Cutter', display)
            key = cv2.waitKey(20) & 0xFF

            if key == ord('n'):
                if len(current_coords) == 2 and current_idx < NUM_BOXES:
                    c = current_coords
                    cuts[BOX_NAMES[current_idx]] = [min(c[0][0], c[1][0]), min(c[0][1], c[1][1]), max(c[0][0], c[1][0]), max(c[0][1], c[1][1])]
                    current_idx += 1
                    current_coords = []

            elif key == ord('z'):
                if len(current_coords) > 0: current_coords.pop()
                elif current_idx > 0:
                    current_idx -= 1
                    del cuts[BOX_NAMES[current_idx]]

            elif key == ord('c'):
                if last_cuts_memory:
                    cuts = last_cuts_memory.copy()
                    current_idx = NUM_BOXES
                    print("Coordinates copied from previous video.")

            elif key == ord('s'):
                if len(cuts) == NUM_BOXES:
                    print("Saving and processing...")
                    cv2.destroyWindow('Cutter')
                    process_video(video_file, os.path.join(VIDEO_PATH, video_file), cuts, subjects)
                    completed_work[video_file] = cuts
                    save_progress(completed_work)
                    last_cuts_memory = cuts 
                    break

            elif key == 27:
                cap.release()
                cv2.destroyAllWindows()
                return

        cap.release()

def process_video(filename, filepath, cuts_dict, subjects_list):
    cap = cv2.VideoCapture(filepath)
    writers = []
    clean_name = os.path.splitext(filename)[0]
    
    for i, (key, coords) in enumerate(cuts_dict.items()):
        subject = subjects_list[i]
        x1, y1, x2, y2 = coords
        w, h = x2 - x1, y2 - y1
        out_name = f"{subject}_{clean_name}.mp4"
        out_full = os.path.join(OUTPUT_PATH, out_name)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writers.append({'writer': cv2.VideoWriter(out_full, fourcc, VIDEO_FPS, (w, h)), 'coords': coords})

    while True:
        ret, frame = cap.read()
        if not ret: break
        for item in writers:
            c = item['coords']
            crop = frame[c[1]:c[3], c[0]:c[2]]
            item['writer'].write(crop)

    cap.release()
    for item in writers: item['writer'].release()
    print("Done.")

if __name__ == "__main__":
    main()