import cv2
import os

# --- CONFIGURATION ---
INPUT_FOLDER = r"../01_video_cropper/output_videos"
OUTPUT_FOLDER = r"output_downsampled"
RESIZE_FACTOR = 0.5  # 0.5 = Half resolution
FRAME_SKIP = 2       # 2 = Keep 1 frame every 2 (e.g., 60fps -> 30fps)
# ----------------------

def main():
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

    print(f"Starting downsampling for {len(files)} videos...")

    for video in files:
        path = os.path.join(INPUT_FOLDER, video)
        cap = cv2.VideoCapture(path)
        
        w, h = int(cap.get(3)), int(cap.get(4))
        fps = cap.get(5)
        
        new_w, new_h = int(w * RESIZE_FACTOR), int(h * RESIZE_FACTOR)
        new_fps = fps / FRAME_SKIP
        
        out_name = f"small_{video}"
        out_path = os.path.join(OUTPUT_FOLDER, out_name)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_path, fourcc, new_fps, (new_w, new_h))
        
        print(f"Processing: {video} -> {new_w}x{new_h} @ {new_fps:.1f}fps")
        
        count = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            if count % FRAME_SKIP == 0:
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                out.write(resized)
            count += 1
            
        cap.release()
        out.release()

if __name__ == "__main__":
    main()