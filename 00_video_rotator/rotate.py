import cv2
import os

# --- CONFIGURATION ---
INPUT_FOLDER = r"C:\Path\To\RawUpsideDownVideos"
OUTPUT_FOLDER = r"output_rotated"
# ---------------------

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Filter for video files
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.avi'))]
    print(f"Found {len(files)} videos to rotate.")

    for video_file in files:
        path_in = os.path.join(INPUT_FOLDER, video_file)
        # Add 'rot_' prefix to avoid overwriting if folders are messed up
        path_out = os.path.join(OUTPUT_FOLDER, f"rot_{video_file}")

        cap = cv2.VideoCapture(path_in)
        if not cap.isOpened():
            print(f"Error opening {video_file}")
            continue

        # Get original properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Setup Writer (Same resolution, same FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path_out, fourcc, fps, (width, height))

        print(f"Rotating: {video_file} (180 degrees)...")
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # ROTATION 180 DEGREES
            rotated_frame = cv2.rotate(frame, cv2.ROTATE_180)
            
            out.write(rotated_frame)
            frame_count += 1
            
            if frame_count % 100 == 0:
                print(f"  -> Processed {frame_count}/{total_frames} frames", end='\r')

        print(f"\nDone: {video_file}")
        cap.release()
        out.release()

    print("All videos rotated successfully.")

if __name__ == "__main__":
    main()