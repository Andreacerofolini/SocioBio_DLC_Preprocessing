# SocioBio DLC Preprocessing Suite

A collection of Python tools designed to streamline the video preprocessing workflow for sociobiology experiments (e.g., 15 Petri dishes recorded simultaneously) before analysis with **DeepLabCut**.

This suite handles:
1.  **Rotation**: Fixing camera orientation.
2.  **Cropping**: Splitting multi-subject videos into single-subject clips (with drift correction).
3.  **Downsampling**: Reducing resolution and FPS for faster AI training.
4.  **Enhancement**: Improving contrast for better tracking.

---

## 🚀 Workflow Overview

Follow this order to prepare your videos:

| Step | Tool Folder | When to use it? |
| :--- | :--- | :--- |
| **0** | `00_video_rotator` | **Only if** the camera was mounted upside-down. |
| **1** | `01_video_cropper` | **Always**. To cut the 15 subjects into individual videos. |
| **2** | `02_video_downsampler` | **Always**. To reduce file size (e.g., 1080p 60fps -> 540p 30fps). |
| **3** | `03_video_enhancer` | **Optional**. Use if the subject is hard to see (low contrast). |

---

## 📋 Prerequisites

### 1. Installation
Install the required Python libraries:
```bash
pip install -r requirements.txt