# Stable Diffusion WebUI – Raspberry Pi 5-Class (ARM)

![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%205--Class%20%2F%20ARM-blue)
![CPU](https://img.shields.io/badge/acceleration-CPU--only-orange)
![ARM64](https://img.shields.io/badge/ARM64-aarch64-success)

Install **AUTOMATIC1111 Stable Diffusion WebUI** on Raspberry Pi 5-class hardware, with a Python virtual environment, four optional model downloads, and CLI or Tkinter launchers. Desktop and menu icons are optional too.

Inference runs on the CPU. The Pi's GPU is not used for generation; patience remains part of the dependency stack.

> **Hardware and OS**
>
> The installer accepts **Raspberry Pi 5, Raspberry Pi 500, and Compute Module 5**, with an **aarch64** OS and at least **4 GiB reported by `/proc/meminfo`**. A nominal 4 GB board may report less and fail this check.
>
> The project targets Raspberry Pi OS 64-bit on Pi 5. The platform check also accepts Pi 500, CM5, and OS IDs `raspbian`, `debian`, and `ubuntu`. Acceptance by that check is not a compatibility guarantee: this bundle has no test matrix covering those boards and OS releases.
>
> Installation and the first LAN-mode launch need internet access. There is **no free-space check**. All four model labels total **10.66 GB**, before WebUI, dependencies, temporary files, and reinstall backups. Allow extra space; the model total is not an installation-space estimate.

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

This runs the current `main` branch. To test changes from a downloaded ZIP, run that local copy instead.

To inspect and run a downloaded bundle, open its directory and use:

```bash
less setup_sd.sh
bash setup_sd.sh
```

Run from your normal account with sudo available. Setup installs system packages; the GUI needs a desktop session and uses Tkinter, Pillow, Zenity, and LXTerminal.

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

Press **S** to open model selection when downloads are enabled. All four models start selected. Use **Up/Down** to move and **Space/Enter** to toggle; the approximate download total changes with your selection. **C** continues, **B** returns to the options, and **Q** quits. Select at least one model, or turn downloads off in the previous menu. Letter controls accept either case.

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

Generation time and memory use depend on the model and image settings. There are no bundled benchmarks, and passing the RAM check does not mean every workload will fit. The launcher uses `--no-half`; FP16 checkpoint filenames describe the downloaded files, not a promise of FP16 inference.

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

The GUI launches LAN and Offline modes without an Enter-to-close wait. The terminal command ends when WebUI exits, including after a successful Stop. **Exit** closes the GUI window without stopping WebUI. To keep launch errors visible, start `run_sd.sh` from an existing terminal.

## 6. Model downloads

Choose one or more of these four checkpoints, or disable model downloads entirely:

**CyberRealistic V7.0 — 2.13 GB**

File: `CyberRealistic_V7.0_FP16.safetensors`

Photorealistic image generation, with a focus on lifelike people, portraits, and scenes. [Model details](https://huggingface.co/cyberdelia/CyberRealistic).

**Realistic Vision V5.1 Inpainting — 4.27 GB**

File: `Realistic_Vision_V5.1-inpainting.safetensors`

Inpainting checkpoint for repairing or replacing masked areas of an existing image, such as a face, object, or background section. [Model details](https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE).

**Realistic Vision V6.0 New Vision B1 — 2.13 GB**

File: `Realistic_Vision_V6.0_NV_B1_fp16.safetensors`

The V6.0 “New Vision” beta checkpoint for realistic, photo-style images, including portraits and full-body subjects; this is the general-generation version. [Model details](https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE).

**Real Dream 16 — 2.13 GB**

File: `sd1.5-real-dream-16.safetensors`

Real Dream's SD 1.5 checkpoint for realistic and photorealistic image generation—another option for exploring a different look with the same prompt. [Model details](https://huggingface.co/sinatra-rd/sd-1.5-real-dream).

The selector totals the rounded sizes shown above: **10.66 GB** with all four enabled. These are fixed labels, not live size lookups. The download title uses the size returned by the host.

Each model downloads in five parallel pieces. The progress display checks terminal width on every refresh, shortens its bars or labels when needed, and leaves the last column clear to avoid wrapping. Progress refreshes about twice a second; speed recalculates after at least one second. Curl errors and status messages can still print separate lines.

Setup checks each piece's size, joins the pieces, then checks the combined file against the SHA-256 in Hugging Face's `x-linked-etag` header. The hash comes from the download host; it is not independently pinned. Curl retries failed requests, and the installer allows up to 20 whole-model attempts.

To supply your own checkpoint, place it under:

```text
<installation root>/stable-diffusion-webui/models/Stable-diffusion/
```

Check the model publisher's license and usage terms. Model selection does not establish compatibility with every checkpoint.

## 7. Uninstall

Run your installation's `run_sd.sh`, select **4**, and confirm with `y` or `yes` followed by Enter. The GUI also offers an uninstall confirmation.

**Back up anything you want to keep first.** Uninstall removes the entire WebUI directory, including models, generated images, extensions, and configuration stored there. It also removes the virtual environment, `run_sd.sh`, GUI helpers, desktop/menu entries, and `.sd-runtime` directory.

Installed icon files and apt packages remain. The pip and desktop configuration changes also remain.

There is no dedicated updater. **Re-running setup replaces the installation.** Setup stages a fresh WebUI checkout, backs up the old WebUI and environment, and deletes those backups after success. Existing models, outputs, extensions, and settings are not migrated. Rollback covers some failures, but not every exit path or system change. Keep your own backup before reinstalling.

## 8. Included files

| File | Purpose |
| --- | --- |
| `setup_sd.sh` | Installer, embedded launchers, and fallback artwork. |
| `sd_gui_banner.png` | Banner used when found alongside a local installer. |
| `sd_icon.png` | Icon used when found alongside a local installer. |
| `README.md` | Installation and usage notes. |
| `validate_bundle.sh` | Static bundle checks. |

Remote setup needs only `setup_sd.sh`; fallback artwork is embedded. The companion PNGs have different dimensions. Local asset lookup happens after setup changes directory, so invoking the script with a relative path can also select the embedded artwork.

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

The supplied ZIP has no Unix executable-mode metadata. If extraction leaves the scripts non-executable, the validator stops at its permission check. To enable direct execution in your local copy:

```bash
chmod +x setup_sd.sh validate_bundle.sh
./validate_bundle.sh
```

The validator checks Bash and GUI Python syntax and looks for a few implementation markers. It does not test the four-model selector, downloads, installation, image generation, rollback, or uninstall. Passing it is a useful first check, not a real Pi test.

### Licensing and attribution

This repository is a community-maintained Raspberry Pi installer and compatibility layer. It does **not** claim ownership of, or relicense, AUTOMATIC1111 Stable Diffusion WebUI, Stable Diffusion, downloaded model checkpoints, Python packages, or system packages. Each third-party component remains subject to the license and usage terms published by its original author or distributor.

| Component | License / attribution |
| --- | --- |
| **AUTOMATIC1111 Stable Diffusion WebUI** | Licensed upstream under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See the [AUTOMATIC1111 license](https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/master/LICENSE.txt). |
| **Stability AI Stable Diffusion code** | The upstream Stable Diffusion codebase is released under the **MIT License**; model weights and related assets may use separate licenses. See the [upstream repository](https://github.com/Stability-AI/stablediffusion). |
| **CyberRealistic V7.0** | Distributed under the license identified by the publisher on the [CyberRealistic model page](https://huggingface.co/cyberdelia/CyberRealistic) (`creativeml-openrail-m`). |
| **Realistic Vision V5.1** | Distributed under the license identified by the publisher on the [Realistic Vision V5.1 model page](https://huggingface.co/SG161222/Realistic_Vision_V5.1_noVAE) (`creativeml-openrail-m`). |
| **Realistic Vision V6.0 B1** | Distributed under the license identified by the publisher on the [Realistic Vision V6.0 B1 model page](https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE) (`creativeml-openrail-m`). |
| **Real Dream 16** | The publisher currently identifies the license as **other**. Review the current terms on the [Real Dream model page](https://huggingface.co/sinatra-rd/sd-1.5-real-dream) before redistribution or commercial use. |
| **Python packages and system dependencies** | Remain under their respective upstream licenses. Installing them through this project does not change those terms. |
| **Project artwork** | `sd_icon.png`, `sd_gui_banner.png`, and the matching embedded fallback artwork were created specifically for this project using **ChatGPT by OpenAI**. They are not copied from AUTOMATIC1111, Stability AI, or the model publishers. OpenAI's [Terms of Use](https://openai.com/policies/terms-of-use/) state that, as between OpenAI and the user and to the extent permitted by applicable law, the user owns the generated output. |

The optional model files are downloaded from their publishers at install time and are **not bundled in this repository**. Users are responsible for reviewing the current model license and usage restrictions before use or redistribution.

The original installer, launcher code, documentation, and project-specific assets in this repository do **not currently have a standalone project license file**. If this project is intended for open-source redistribution, a separate `LICENSE` file should be added for the original project material. That license would not replace or override any of the third-party licenses listed above.

This project is community-maintained and is not an official AUTOMATIC1111, Stability AI, Hugging Face, or OpenAI project, and inclusion of a name or link above does not imply endorsement.
