# 🐜 SocioBio DLC Preprocessing Suite

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green?logo=opencv&logoColor=white)
![Status](https://img.shields.io/badge/Maintenance-Active-success)

A complete Python tool suite for preprocessing multi-subject videos used in sociobiology experiments (e.g., multi-well Petri dish assays) prior to analysis with **DeepLabCut**.

---

## ⚡ 3-Minute Quick Start

Want to run everything immediately? Follow these three steps.

### 1. Install Dependencies
Open a terminal in the project folder and run:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Open `config_local.py` and modify **only** the path to your raw videos:
```python
# Inside config_local.py
INPUT_ROTATOR_PATH = r"D:\Path\To\My\Raw\Videos"
```

### 3. Run the Pipeline
Execute the following scripts in order:

#### A. Rotation & Downsampling (video preparation)
```bash
python 00_video_rotator/rotate.py
```
Controls:
- **R** → toggle 180° rotation
- **SPACE** → process video
- **ESC** → quit

#### B. Subject Cropping
```bash
# Use crop_drift.py if the camera moved; otherwise crop_static.py
python 01_video_cropper/crop_drift.py
```
> Ensure the `rename_list_coldhardiness.csv` file is correctly filled.

#### C. Enhancement (optional)
```bash
python 03_video_enhancer/enhance.py
```

---

## ✨ Key Features

| Module | Description |
|--------|-------------|
| 🔄 **Smart Rotator** | Rotation (180°), 50% downsampling, and frame reduction (60→30 fps) in a single pass. |
| ✂️ **Drift-Aware Cropper** | Splits multi-subject grid videos into individual clips with automatic drift correction. |
| 👁️ **Contrast Booster** | Enhances visibility of transparent insects using CLAHE filtering. |

---

## 🗺️ Workflow Overview

```mermaid
graph TD
    A[🎥 Raw Videos (SD Card)] -->|Input| B(00_rotate.py);
    style A fill:#f9f,stroke:#333,stroke-width:2px

    B -->|Resize & Rotate| C[📂 Output Preprocessed];

    C --> D{Is Camera Static?};

    D -- Yes (Tripod) --> E[01_crop_static.py];
    D -- No (Vibration) --> F[01_crop_drift.py];

    E & F -->|Read CSV & Cut| G[📂 Output Cropped];

    G --> H(03_enhance.py);
    H -->|CLAHE Filter| I[🏁 Final Output];
    style I fill:#9f9,stroke:#333,stroke-width:2px
```

---

## 📂 Project Structure

```
📦 Project Root
 ├── ⚙️ config_local.py               <- CENTRAL CONFIG (Only edit this!)
 ├── 📜 rename_list_coldhardiness.csv <- Metadata for subject renaming
 ├── 📜 requirements.txt              <- Python dependencies
 ├── 📂 00_video_rotator/             <- Step 1: Preparation & Optimization
 ├── 📂 01_video_cropper/             <- Step 2: Subject extraction
 └── 📂 03_video_enhancer/            <- Step 3: Contrast enhancement
```

---

## 🚀 Detailed Usage Guide

### 🥇 Step 1 — Preparation (`rotate.py`)
Entry script that reduces file size, fixes orientation, and prepares videos for DeepLabCut.

Operations:
- 50% resize
- Frame skip (60 → 30 fps)
- Optional 180° rotation

Controls:
- **R** → toggle rotation
- **SPACE** → process
- **ESC** → exit

---

### 🥈 Step 2 — Cropping (`crop_*.py`)
Splits the grid into individual subject videos using your metadata CSV.

#### Option A — Static Crop (`crop_static.py`)
- Use when the camera was stable (tripod)
- Draw the grid once
- The crop is applied uniformly to all frames

#### Option B — Drift Correction (`crop_drift.py`)
- Use when the camera had vibrations or movement
- Computes optical flow frame-by-frame
- Dynamically adjusts the crop window to keep subjects aligned

---

### 🥉 Step 3 — Enhancement (`enhance.py`)
Improves videos with low contrast or transparent subjects.

Applies CLAHE (Contrast Limited Adaptive Histogram Equalization).

Default settings:
```
CLIP_LIMIT = 3.0
```

---

## 📝 Metadata CSV Format

The file `rename_list_coldhardiness.csv` must follow this structure:

```
filename,subject_1,subject_2,...
VIDEO_01.mp4,ant_A,ant_B,...
VIDEO_02.mp4,ant_C,ant_D,...
```

> The number of `subject_*` columns must match the `NUM_BOXES` value in the crop script.

---

## ✅ Ready to Use!
This suite is designed to be simple, robust, and seamlessly integrated into your DeepLabCut workflow.

Happy processing! 🐜
