import cv2
import os
from tqdm import tqdm 
import sys 

# Import config locale
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_local import INPUT_ROTATOR_PATH

# --- CONFIGURATION ---
INPUT_FOLDER = INPUT_ROTATOR_PATH 
OUTPUT_FOLDER = r"output_preprocessed" 

# SETTINGS OTTIMIZZAZIONE
RESIZE_FACTOR = 0.5  # 0.5 = Dimezza risoluzione (1080p -> 540p)
FRAME_SKIP = 2       # 2 = 30fps (da 60fps originali)
# ---------------------

def get_user_choices(files):
    """ Fase 1: Check Visivo Rapido """
    choices = {}
    print("\n" + "="*60)
    print(" FASE 1: CHECK ROTAZIONE")
    print(" [r]     -> Ruota 180°")
    print(" [SPAZIO]-> Conferma e vai al prossimo")
    print(" [ESC]   -> Esci")
    print("="*60 + "\n")
    
    for i, video_file in enumerate(files):
        path_in = os.path.join(INPUT_FOLDER, video_file)
        cap = cv2.VideoCapture(path_in)
        if not cap.isOpened(): continue
        
        ret, frame = cap.read()
        cap.release()
        if not ret: continue

        # Resize per anteprima
        preview_h = 600
        h, w = frame.shape[:2]
        ratio = preview_h / h
        preview_w = int(w * ratio)
        preview_frame = cv2.resize(frame, (preview_w, preview_h))
        
        rotate_flag = False 
        
        print(f"Check ({i+1}/{len(files)}): {video_file}")

        while True:
            display_img = preview_frame.copy()
            if rotate_flag:
                display_img = cv2.rotate(display_img, cv2.ROTATE_180)
                status_text = "RUOTATO (Premi SPAZIO)"
                color = (0, 0, 255)
            else:
                status_text = "ORIGINALE (Premi 'r' o SPAZIO)"
                color = (0, 255, 0)

            cv2.putText(display_img, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.imshow('Setup Rotazione', display_img)
            
            key = cv2.waitKey(0) & 0xFF
            
            if key == ord('r'):
                rotate_flag = not rotate_flag 
            elif key == 32 or key == 13: # Spazio o Invio
                choices[video_file] = rotate_flag
                break
            elif key == 27: # Esc
                cv2.destroyAllWindows()
                sys.exit("Uscita forzata.")
    
    cv2.destroyAllWindows()
    return choices

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.avi'))]
    if not files:
        print(f"ERRORE: Nessun video trovato in: {INPUT_FOLDER}")
        return

    # --- FASE 1 ---
    rotation_map = get_user_choices(files)

    print("\n" + "="*60)
    print(" FASE 2: ELABORAZIONE BATCH")
    print(" Siediti e rilassati. Sto lavorando.")
    print("="*60)

    # --- FASE 2 ---
    for i, video_file in enumerate(files):
        if video_file not in rotation_map: continue
        
        should_rotate = rotation_map[video_file]
        path_in = os.path.join(INPUT_FOLDER, video_file)
        path_out = os.path.join(OUTPUT_FOLDER, f"proc_{video_file}")

        cap = cv2.VideoCapture(path_in)
        
        # Info video
        w_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h_orig = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps_orig = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        new_w = int(w_orig * RESIZE_FACTOR)
        new_h = int(h_orig * RESIZE_FACTOR)
        new_fps = fps_orig / FRAME_SKIP

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path_out, fourcc, new_fps, (new_w, new_h))

        # Descrizione azione per la barra
        action_tag = "[ROT]" if should_rotate else "[STD]"
        desc_text = f"Video {i+1}/{len(files)} {action_tag}"

        count = 0
        
        # --- QUI C'È LA BARRA DI PROGRESSO ---
        # total=total_frames permette di calcolare la %
        # unit='fr' indica che contiamo frame
        with tqdm(total=total_frames, desc=desc_text, unit='fr', ncols=100) as pbar:
            while True:
                ret, frame = cap.read()
                if not ret: break
                
                # Scriviamo solo se il frame è quello giusto (Frame Skipping)
                if count % FRAME_SKIP == 0:
                    if should_rotate:
                        frame = cv2.rotate(frame, cv2.ROTATE_180)
                    
                    resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    out.write(resized_frame)

                count += 1
                pbar.update(1) # Aggiorna la barra di 1 frame
        
        cap.release()
        out.release()

    print("\n" + "="*60)
    print(" TUTTO COMPLETATO CON SUCCESSO!")
    print(" Ora puoi lanciare lo script 01_video_cropper.")
    print("="*60)

if __name__ == "__main__":
    main()