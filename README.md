# Stable Diffusion WebUI – Raspberry Pi 5-Class (ARM)

![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%205--Class%20%2F%20ARM-blue)
![CPU](https://img.shields.io/badge/acceleration-CPU--only-orange)
![ARM64](https://img.shields.io/badge/ARM64-aarch64-success)

An interactive installer for **AUTOMATIC1111 Stable Diffusion WebUI** on Raspberry Pi 5-class hardware. It sets up a Python virtual environment, optional model downloads, a terminal launcher, and an optional Tkinter GUI with desktop and menu icons.

Inference runs on the CPU. The Pi's GPU is not used for generation; patience remains part of the dependency stack.

> **Hardware and OS**
>
> The installer accepts **Raspberry Pi 5, Raspberry Pi 500, and Compute Module 5**, with an **aarch64** OS and at least **4 GiB reported by `/proc/meminfo`**. A nominal 4 GB board may report less and fail this check.
>
> Raspberry Pi OS 64-bit on Pi 5 is the environment previously reported working in this project's documentation. The code also accepts OS IDs `raspbian`, `debian`, and `ubuntu`, but that check does not establish compatibility with every release. Pi 500, CM5, and other accepted OS combinations still need recorded testing.
>
> Installation and the first LAN-mode launch need internet access. There is **no free-space check** in this version. Allow room for the environment, WebUI, models, temporary download pieces, and any existing installation retained during replacement. No measured minimum disk requirement is established here.

---

## Index

1. [Remote install](#1-remote-install)
2. [Interactive installer](#2-interactive-installer)
3. [Running Stable Diffusion](#3-running-stable-diffusion)
4. [First launch](#4-first-launch)
5. [GUI launcher](#5-gui-launcher)
6. [Model downloads](#6-model-downloads)
7. [Uninstall](#7-uninstall)
8. [Included files](#8-included-files)
9. [Notes](#9-notes)

## 1. Remote install

```bash
curl -sSL https://raw.githubusercontent.com/comp6062/rpi-automatic1111/main/setup_sd.sh | bash
```

This runs the script from the repository's current `main` branch. It does not run a separately downloaded or locally edited copy.

To inspect and run a downloaded bundle, open its directory and use:

```bash
less setup_sd.sh
bash setup_sd.sh
```

Run from your normal desktop account with sudo available. The script uses sudo for system packages and selected setup commands. A desktop session is needed for the GUI, which uses Tkinter, Pillow, Zenity, and LXTerminal.

**Before installing:** the script removes lines containing `piwheels` from user and system pip configuration. With the GUI enabled, it also sets `quick_exec=1` in libfm/PCManFM configuration. These settings affect more than this application and are not restored on uninstall.

Back up an existing installation before running setup again; see [Uninstall](#7-uninstall) for the reinstall and data-removal details.

## 2. Interactive installer

The initial menu looks like this with the defaults enabled and `/home/admin` as the user's home:

```text
Stable Diffusion Raspberry Pi Installer
=======================================
Use the menu below to choose install options.

  1) Download included models:  ON
  2) Install GUI launcher:      ON
     (reboot required)
  3) Create desktop icon:       ON
  4) Create menu launcher:      ON
  5) Install files location:    /home/admin

  S) Start install
  Q) Quit
```

Press a number without Enter to change an option. Disabling the GUI also disables both icons; enabling it again enables both. Option 5 accepts a custom installation directory, with Tab completion for existing paths. Setup creates the selected directory if needed.

Press **S** to continue. With downloads enabled, use **Up/Down** to select a model and **Space/Enter** to toggle it. **C** continues, **B** returns to the options, and **Q** quits. At least one model must be selected while downloads are enabled. Letter controls accept either case.

The summary lists the installation path, selected models, and launcher options. Confirm with **Y** or Enter; other keys cancel. With the GUI enabled, setup finishes with a single-key reboot prompt: **Y** reboots; other keys skip it.

The default installation root is your home directory. The main installed files are:

```text
~/stable-diffusion-webui/
~/stable-diffusion-env/
~/run_sd.sh
```

A custom root moves these together. Desktop and menu entries still live in your user's home directory and point to the selected root.

## 3. Running Stable Diffusion

```bash
~/run_sd.sh
```

For a custom root:

```bash
/path/to/install/run_sd.sh
```

The terminal menu reads a choice followed by Enter:

| Choice | Action |
| --- | --- |
| `1` | LAN mode: starts WebUI and permits dependency setup. |
| `2` | Offline mode: starts with `--skip-install`. |
| `3` | Stop running: checks the recorded PID, working directory, and command before stopping WebUI. |
| `4` | Uninstall: asks for confirmation, then removes the installation. |
| `q` | Quit. |

Both launch modes use `--listen` and port **7860**. Open `http://127.0.0.1:7860` on the Pi, or `http://<Pi-IP>:7860` from another device. The launcher does not configure authentication. Use it on a trusted network; **Offline mode still listens on the network**.

## 4. First launch

Start in **LAN mode** with internet access so WebUI can finish its runtime setup. After that succeeds, use **Offline mode** to skip installation checks. It is not a network-isolation mode, and extensions or missing assets may still need internet access.

Generation time and memory use depend on the model and image settings. This bundle includes no measured benchmarks or guarantee that every model will fit in memory. The launcher uses `--no-half`; FP16 checkpoint filenames describe the downloaded files, not a promise of FP16 inference.

## 5. GUI launcher

With the GUI enabled, setup writes these files under the installation root:

```text
.sd_gui_app.py
.sd_gui_runner.sh
.sd_gui_banner.png
```

The optional desktop icon is `~/Desktop/StableDiffusionGUI.desktop`. The menu entry is `~/.local/share/applications/sd-gui.desktop`, under **Applications → Graphics → Stable Diffusion** where the desktop supports that category.

Icons are installed at:

```text
~/.local/share/icons/sd_icon.png
~/.local/share/icons/hicolor/256x256/apps/sd_icon.png
```

The GUI offers LAN Mode, Offline Mode, Stop Running, Uninstall, and Open Web-UI. LAN launch waits for WebUI to respond and then opens the browser. Offline launch does not automatically open it; use **Open Web-UI**.

When Chromium is available, the GUI opens a separate app window with an installation-specific browser profile. **Stop WebUI** also attempts to close that browser process group. The default-browser fallback is not tracked and may stay open.

When launched from the GUI, LAN and Offline terminals close automatically when WebUI exits, including after Stop; there is no Enter-to-close wait. **Exit** closes the GUI window without stopping WebUI.

## 6. Model downloads

Choose any combination of the four included checkpoints:

| File | Menu size | Use |
| --- | --- | --- |
| `CyberRealistic_V7.0_FP16.safetensors` | 2.13 GB | General image generation. |
| `Realistic_Vision_V5.1-inpainting.safetensors` | 4.27 GB | Inpainting. |
| `Realistic_Vision_V6.0_NV_B1_fp16.safetensors` | 2.13 GB | General image generation. |
| `sd1.5-real-dream-16.safetensors` | 2.13 GB | General image generation. |

Downloads use five parallel byte ranges, display progress on one row, and update the speed calculation at roughly one-second intervals. The download title uses the size returned by the host; menu sizes are fixed labels.

Each piece is checked for size. The combined file is checked against the SHA-256 value supplied by Hugging Face's `x-linked-etag` header before activation. This detects mismatched downloads, but the hash comes from the same host and is not pinned independently in the installer. Downloads have curl retries plus up to 20 whole-model attempts.

To supply your own checkpoint, place it under:

```text
<installation root>/stable-diffusion-webui/models/Stable-diffusion/
```

Check the model publisher's license and usage terms. Model selection does not establish compatibility with every checkpoint.

## 7. Uninstall

Run your installation's `run_sd.sh`, select **4**, and confirm with `y` or `yes` followed by Enter. The GUI also offers an uninstall confirmation.

**Back up anything you want to keep first.** Uninstall removes the entire WebUI directory, including models, generated images, extensions, and configuration stored there. It also removes the virtual environment, `run_sd.sh`, GUI helpers, desktop/menu entries, and `.sd-runtime` directory.

Installed icon files and apt packages remain. The pip and desktop configuration changes also remain.

There is no dedicated updater. **Re-running setup is a replacement install:** it stages a fresh WebUI checkout, backs up the old WebUI and environment, creates the new environment at its final path, and deletes the backups on success. It does not migrate existing models, outputs, extensions, or settings. Error rollback exists, but does not cover every failure or restore all launcher and system changes. Keep a separate backup before reinstalling.

## 8. Included files

| File | Purpose |
| --- | --- |
| `setup_sd.sh` | Installer, embedded launchers, and fallback artwork. |
| `sd_gui_banner.png` | Banner used when found alongside a local installer. |
| `sd_icon.png` | Icon used when found alongside a local installer. |
| `README.md` | Installation and usage notes. |
| `validate_bundle.sh` | Static bundle checks. |

Remote setup needs only `setup_sd.sh`. Its embedded artwork has different dimensions from the companion PNG files. Relative-path invocation may also fall back to the embedded assets after setup changes directory, so local and remote installations can use different artwork. Neither version was changed in the maintenance pass.

## 9. Notes

WebUI is pinned to commit `82a973c04367123ae98bd9abdf80d9eda9b910e2`. Setup redirects the Stable Diffusion repository URL to `comp6062/Stability-AI-stablediffusion`, adjusts the CLIP installation command, and pins several Python dependencies. Other dependencies remain unpinned, so future installs may resolve different versions.

Setup installs apt dependencies without a full OS upgrade. Runtime PID files live under `<installation root>/.sd-runtime`; desktop entry names and installed icon names are shared across installations for the same user.

### Troubleshooting

- **Platform rejected:** check `uname -m`, `/proc/device-tree/model`, `/etc/os-release`, and `MemTotal` in `/proc/meminfo`. The installer checks the reported values, not the board's advertised RAM.
- **Model download fails:** keep the terminal error, check connectivity and disk space, and note whether the failure mentions headers, piece size, or SHA-256. Setup does not provide a persistent download-resume interface.
- **WebUI fails to launch:** capture the terminal traceback. Use LAN mode for initial dependency setup. “Installation is incomplete” means the launcher could not find its Python executable or `launch.py`.
- **GUI or icon does not launch:** follow setup's reboot instruction, then run `<installation root>/.sd_gui_runner.sh` from a desktop terminal to see errors. The installer assumes a literal `~/Desktop` directory.
- **Launch error disappears when the terminal closes:** run `<installation root>/run_sd.sh` from an existing terminal to keep the error output visible.

### Bundle validation

```bash
bash validate_bundle.sh
```

The supplied archive has no Unix executable-mode metadata and extracts here with both shell scripts non-executable. The validator therefore stops at its executable check. To make a local validation copy executable:

```bash
chmod +x setup_sd.sh validate_bundle.sh
./validate_bundle.sh
```

The validator checks Bash and embedded GUI Python syntax, then looks for selected implementation markers. It does not perform an installation, generate an image, or prove rollback and uninstall behavior. Real Pi testing is still required before submission.

### Licensing

This bundle contains no project license file. A license for the installer and permission to redistribute its artwork need to be established before presenting it as a ready-to-submit open-source release. WebUI, dependencies, and model files have their own terms; this README does not grant rights to them.
