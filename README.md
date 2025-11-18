# SocioBio DLC Preprocessing Suite

A collection of Python tools designed to streamline the video preprocessing workflow for sociobiology experiments (e.g., multiple Petri dishes recorded simultaneously) before analysis with **DeepLabCut**.

This suite handles:
1.  **Rotation**: Fixing camera orientation (if mounted upside-down).
2.  **Cropping**: Splitting multi-subject videos into single-subject clips (with optional drift correction).
3.  **Downsampling**: Reducing resolution and FPS for faster AI training.
4.  **Enhancement**: Improving contrast for better tracking in low-visibility conditions.

---

## 🚀 Workflow Overview

Follow this order to prepare your videos:

| Step | Tool Folder | Script | When to use it? |
| :--- | :--- | :--- | :--- |
| **0** | `00_video_rotator` | `rotate.py` | **Only if** the camera was mounted upside-down. |
| **1** | `01_video_cropper` | `crop_static.py` OR `crop_drift.py` | **Always**. To cut the original video into individual subjects. |
| **2** | `02_video_downsampler` | `downsample.py` | **Always**. To reduce file size (e.g., 1080p 60fps -> 540p 30fps). |
| **3** | `03_video_enhancer` | `enhance.py` | **Optional**. Use if the subject is transparent or hard to see. |

---

## 📋 Prerequisites

### 1. Installation
Install the required Python libraries using the provided requirements file:
```bash
pip install -r requirements.txt