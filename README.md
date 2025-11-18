# SocioBio DLC Preprocessing Tools

A collection of Python scripts designed to preprocess video data from sociobiology experiments (e.g., multiple Petri dishes) for analysis with **DeepLabCut**.

## 📂 Repository Structure

* **01_video_cropper**: Tools to crop a single video containing multiple subjects (e.g., 15 Petri dishes) into individual video files per subject. Includes metadata integration via Excel.
* **02_video_downsampler**: Batch processing tool to reduce resolution and framerate (FPS) to speed up DeepLabCut training and analysis.
* **03_video_enhancer**: Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) to improve subject visibility in low-contrast environments.

## 🚀 Recommended Workflow

1.  **Crop**: Isolate individual subjects from the raw footage.
2.  **Downsample**: Reduce video size to manageable dimensions (e.g., 640px, 30fps).
3.  *(Optional)* **Enhance**: If contrast is poor, apply the CLAHE filter.
4.  **DeepLabCut**: Import the final processed videos for frame extraction and training.

> **DeepLabCut Note**: Always train your model on videos with the same resolution and FPS as the ones you intend to analyze. Do not train on high-res videos and analyze low-res ones.

---

## 🛠️ Installation

Ensure you have Python installed. Install the required dependencies:

```bash
pip install -r requirements.txt