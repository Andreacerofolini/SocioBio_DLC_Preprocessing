import cv2
import os
import numpy as np

# --- CONFIGURATION ---
INPUT_FOLDER = r"../02_video_downsampler/output_downsampled"
OUTPUT_FOLDER = r"output_enhanced"
CLIP_LIMIT = 3.0       # Higher = more contrast
GRID_SIZE = (8, 8)     # CLAHE grid size
# ----------------------

def apply_clahe(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=CLIP_LIMIT, tileGridSize=GRID_SIZE)
    cl = clahe.apply(l)
    
    merged = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

def main():
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

    print(f"Enhancing contrast for {len(files)} videos...")

    for video in files:
        path = os.path.join(INPUT_FOLDER, video)
        cap = cv2.VideoCapture(path)
        
        w, h = int(cap.get(3)), int(cap.get(4))
        fps = cap.get(5)
        
        out_name = f"enhanced_{video}"
        out_path = os.path.join(OUTPUT_FOLDER, out_name)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
        
        print(f"Processing: {video}")
        
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            enhanced_frame = apply_clahe(frame)
            out.write(enhanced_frame)
            
        cap.release()
        out.release()
    print("Done.")

if __name__ == "__main__":
    main()