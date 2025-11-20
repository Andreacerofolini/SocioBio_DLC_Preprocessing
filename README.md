# SocioBio DLC Preprocessing Suite

A comprehensive Python toolset designed to streamline the video preprocessing workflow for sociobiology experiments (e.g., multiple Petri dishes recorded simultaneously) prior to **DeepLabCut** analysis.

This suite automates:
1.  **Rotation & Downsampling**: Fixing orientation and reducing resolution/FPS for efficient processing.
2.  **Cropping**: Splitting multi-subject videos into individual clips (with **Drift Correction** support).
3.  **Enhancement**: Applying CLAHE contrast improvement for low-visibility recordings.

---

## 📂 Project Structure

Based on the current configuration, your project is organized as follows:

```text
Root/
├── 00_video_rotator/
│   ├── rotate.py               # Handles Rotation, Resizing and Frame Skipping
│   └── output_preprocessed/    # Intermediate output
├── 01_video_cropper/
│   ├── crop_static.py          # Standard fixed-position cropping
│   ├── crop_drift.py           # Cropping with automatic drift compensation
│   └── output_cropped/         # Individual subject videos
├── 03_video_enhancer/
│   ├── enhance.py              # Contrast enhancement (CLAHE)
│   └── output_enhanced/        # Final result (optional)
├── config_local.py             # CENTRAL CONFIGURATION FILE
├── requirements.txt            # Python dependencies
├── rename_list_coldhardiness.csv # Metadata for file naming
└── README.md