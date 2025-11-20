# 🐜 SocioBio DLC Preprocessing Suite

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green?logo=opencv&logoColor=white)
![Status](https://img.shields.io/badge/Maintainance-Active-success)

A comprehensive Python toolset designed to streamline video preprocessing for sociobiology experiments (e.g., multiple Petri dishes) prior to **DeepLabCut** analysis.

---

## ⚡ Key Features

| Module | Description |
| :--- | :--- |
| 🔄 **Smart Rotator** | Handles **Rotation (180°)**, **Downsampling (50%)**, and **Frame Skipping** (60fps→30fps) in a single pass. |
| ✂️ **Drift-Aware Cropper** | Cuts multi-subject grids into single videos. Includes **Automatic Drift Correction** for vibrating cameras. |
| 👁️ **Contrast Booster** | Applies CLAHE enhancement to improve visibility of transparent subjects (e.g., larvae). |

---

## 🗺️ Workflow Overview

How data flows through the suite:

```mermaid
graph TD
    A[🎥 Raw Videos SD Card] -->|Input| B(00_rotate.py);
    style A fill:#f9f,stroke:#333,stroke-width:2px
    
    B -->|Resize & Rotate| C[📂 Output Preprocessed];
    
    C --> D{Is Camera Static?};
    
    D -- Yes (Tripod) --> E[01_crop_static.py];
    D -- No (Vibrations) --> F[01_crop_drift.py];
    
    E & F -->|Read CSV & Cut| G[📂 Output Cropped];
    
    G --> H(03_enhance.py);
    H -->|CLAHE Filter| I[🏁 Final Output];
    style I fill:#9f9,stroke:#333,stroke-width:2px