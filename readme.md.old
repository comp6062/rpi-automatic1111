# Stable Diffusion WebUI – Raspberry Pi (ARM)

![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20%2F%20ARM-blue)
![CPU](https://img.shields.io/badge/acceleration-CPU--only-orange)
![ARM64](https://img.shields.io/badge/ARM64-aarch64-success)
![ARM32](https://img.shields.io/badge/ARM32-armv7l-yellow)
![License](https://img.shields.io/badge/license-MIT-informational)

This repository provides a **fully automated setup** for running  
**AUTOMATIC1111 Stable Diffusion WebUI** (AI image generator), on Raspberry Pi and other ARM-based Linux systems.

It supports **CPU-only inference**, is optimized for ARM environments, and includes
a guided installer, unified launcher, and clean uninstall process.

---

## Table of Contents

- [Overview](#overview)
- [Supported Architectures](#supported-architectures)
  - [ARM64 aarch64 recommended](#arm64-aarch64-recommended)
  - [ARM32 armv7l best-effort](#arm32-armv7l-best-effort)
- [Architecture Detection & Install Logic](#architecture-detection--install-logic)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Model Download Control (Setup Script)](#model-download-control-setup-script)
- [Running Stable Diffusion](#running-stable-diffusion)
- [Offline Mode](#offline-mode)
- [Uninstalling](#uninstalling)
- [Known Limitations](#known-limitations)
- [Credits](#credits)
- [Recommendation Summary](#recommendation-summary)

---

## Overview

This setup installs and configures:

- AUTOMATIC1111 Stable Diffusion WebUI
- Python virtual environment
- CPU-only PyTorch (no CUDA / no ROCm)
- Unified launcher (`~/run_sd.sh`)
- Clean uninstall script (`~/remove.sh`)

Designed for **Raspberry Pi OS**, **Debian**, and other ARM Linux distributions.

---

## Supported Architectures

The installer **automatically detects your CPU architecture** and installs the
appropriate PyTorch build.

---

### ARM64 aarch64 recommended

This is the **preferred and most reliable configuration**.

**Details:**
- Uses **official CPU-only PyTorch wheels**
- Installed from the official PyTorch CPU index
- Fully compatible with modern Python versions

**Why ARM64 is recommended:**
- Faster installation
- Fewer dependency issues
- Better performance
- Works best on Raspberry Pi 4 / 5 (64-bit OS)

---

### ARM32 armv7l best-effort

ARM32 (32-bit Raspberry Pi OS) support is provided on a **best-effort basis**.

**How it works:**
- Installs **prebuilt ARM32 wheels** for:
  - `torch`
  - `torchvision`
  - `numpy` (when available)
- Wheels are sourced from:
  **PINTO0309 / pytorch4raspberrypi**
- Python version is matched dynamically (e.g. `cp39`, `cp310`)

**Limitations:**
- Not all Python versions have matching wheels
- Significantly slower than ARM64
- Higher memory pressure

**If matching wheels are unavailable:**
- Installation stops with a clear error
- You are instructed to switch to a **64-bit OS**

---

## Architecture Detection & Install Logic

This setup script performs **automatic architecture detection** and selects the
best possible installation path for your system **without user input**.

### Detection Process

At runtime, the installer checks:

```bash
uname -m
```

Based on the result:

| Detected value | Installation path |
|---------------|-------------------|
| `aarch64` | ARM64 (official PyTorch CPU wheels) |
| `armv7l`, `armv7*` | ARM32 (prebuilt community wheels) |
| Other | Installation stops (unsupported) |

### Installation Behavior

- **ARM64 systems**
  - Use the official PyTorch CPU wheel index
  - Fully supported and recommended
- **ARM32 systems**
  - Attempt installation using matching prebuilt wheels
  - If compatible wheels are not available, the installer **fails cleanly**
  - No source builds or partial installs are attempted

This ensures the system is **never left in a broken or undefined state**.

---

## System Requirements

### Minimum
- Raspberry Pi 4 / 5 or other ARM SBC
- 4 GB RAM (8 GB recommended)
- Internet connection (for install)

### Strongly Recommended
- **64-bit Raspberry Pi OS**

### Required Packages
- `python3`
- `python3-venv`
- `git`
- `curl`
- `wget`

---

## Installation

Install everything with **one command**:

```bash
curl -sSL https://raw.githubusercontent.com/comp6062/rpi-automatic1111/main/setup_sd.sh | bash
```

Or using `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/comp6062/rpi-automatic1111/main/setup_sd.sh | bash
```

### The installer will

- Install system dependencies
- Create a Python virtual environment
- Clone AUTOMATIC1111 Stable Diffusion WebUI
- Install Python requirements
- Download default models
- Create `~/run_sd.sh` and `~/remove.sh`

---

# Model Download Control (Setup Script)

## Default Model Download Behavior

By default, the setup script **automatically downloads a small set of example Stable Diffusion models** during installation.  
This allows the WebUI to be used immediately after setup completes.


---


## Enable Model Downloads (Default)

To enable model downloads (or re-enable them), ensure the lines are **not commented out**.

### Enabled (Download Models During Setup)


```bash
MODEL1_PATH="$WEBUI_DIR/models/Stable-diffusion/CyberRealistic_V7.0_FP16.safetensors"
MODEL1_URL="https://huggingface.co/cyberdelia/CyberRealistic/resolve/main/CyberRealistic_V7.0_FP16.safetensors"
MODEL2_PATH="$WEBUI_DIR/models/Stable-diffusion/Realistic_Vision_V5.1-inpainting.safetensors"
MODEL2_URL="https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE/resolve/main/Realistic_Vision_V5.1-inpainting.safetensors"
```

When enabled:
- Missing models are downloaded automatically
- Existing models are never overwritten
- Setup remains non-interactive


---
## Disable Model Downloads During Setup

If you prefer to **skip downloading models during installation** (for example, for offline systems or when supplying your own models), you can disable this behavior.

### How to Disable

1. Open the setup script:
   ```bash
   nano setup_sd.sh
   ```

2. Locate the model download section.

3. Comment out the two download lines as shown below.

### Disabled (No Model Downloads)
```bash
#MODEL1_PATH="$WEBUI_DIR/models/Stable-diffusion/CyberRealistic_V7.0_FP16.safetensors"
#MODEL1_URL="https://huggingface.co/cyberdelia/CyberRealistic/resolve/main/CyberRealistic_V7.0_FP16.safetensors"
#MODEL2_PATH="$WEBUI_DIR/models/Stable-diffusion/Realistic_Vision_V5.1-inpainting.safetensors"
#MODEL2_URL="https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE/resolve/main/Realistic_Vision_V5.1-inpainting.safetensors"
```

When disabled:
- No models are downloaded during setup
- Installation still completes normally
- The WebUI will start without errors
- Models can be added later manually

---

## Adding Models Manually (Optional)

If model downloads are disabled, place your `.ckpt` or `.safetensors` files in:

```bash
~/stable-diffusion-webui/models/Stable-diffusion/
```

Restart the WebUI after adding new models.



---

## Running Stable Diffusion

Launch the unified launcher:

```bash
~/run_sd.sh
```

Then:

1. Select **LAN** or **Offline** mode
2. Open the printed URL in your browser
3. Start generating images

---

## Offline Mode

Offline mode runs Stable Diffusion **without internet access**:

- Uses already downloaded models
- Skips package installation and updates
- Accessible at:

```
http://127.0.0.1:7860
```

---

## Uninstalling

To completely remove everything:

```bash
~/remove.sh
```

---

## Known Limitations

- CPU-only inference (no GPU acceleration)
- ARM32 is slower and less stable
- Large models may exceed available RAM
- First generation can take several minutes on Raspberry Pi hardware

---

## Credits

- AUTOMATIC1111 – Stable Diffusion WebUI
- PyTorch Team – CPU wheel support
- PINTO0309 – Raspberry Pi ARM32 PyTorch wheels
- Raspberry Pi community

---

## Recommendation Summary

| Architecture | Status |
|-------------|--------|
| ARM64 (aarch64) | Fully supported (recommended) |
| ARM32 (armv7l) | Best effort only |

If installation fails on ARM32, switch to a **64-bit OS**.  
That is the intended and supported upgrade path.
