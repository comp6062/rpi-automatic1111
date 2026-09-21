# Reference app examinations

From the supplied `piapps-apps-full.zip`: 1,784 files across 260 app/template directories. These three app folders were read in full, their scripts syntax-checked, and their icons decoded. They were not installed.

## 1. Complete examination: Ollama GUI

Seven files: `install-64`, `uninstall`, `description`, `website`, `credits`, `icon-24.png`, `icon-64.png`.

### Installation flow

1. Calls `install_packages python3-tk python3-ttkthemes` to register package dependencies through Pi-Apps.
2. Creates a temporary directory and checks `/usr/local/lib/ollama/pi-apps-v2`. That sentinel skips reinstallation of the model runtime unless its packaging version changes.
3. If needed, removes the old runtime, streams the latest ARM64 archive through tar into `/usr/local`, checks both pipeline exit codes using `PIPESTATUS`, and writes the sentinel.
4. Repairs/creates the `ollama` account and home, adds the desktop user to its group, writes `ollama.service`, reloads systemd, then enables and restarts the service. `Nice=5` lowers its CPU scheduling priority.
5. Uses `git_clone` for Botspot's GUI fork. Creates a runner that starts Python and stops loaded models after the GUI exits. Moves the GUI to `/opt/ollama-gui`.
6. Creates a system desktop entry in Education and installs the supplied 64-pixel icon under `/usr/local/share/icons`; refreshes icon caches.
7. If no models exist, conditionally downloads two featured models when RAM and disk thresholds pass. A failed model pull warns rather than deliberately failing the whole installation.

### Uninstall and update

Removes the GUI, desktop entry, and installed icon. If the argument is `update`, it retains the Ollama runtime, service, account, and model home. Otherwise it disables/stops the service and removes those components, including `/usr/share/ollama`. Finally it calls `purge_packages`.

### Metadata and assets

The description explains local inference, expected slowness, featured models, RAM limitations, GUI and CLI launch commands. Website points to Ollama; credits identify Botspot. Both icons are valid grayscale-with-alpha PNGs, 24×24 and 64×64.

### What transfers to your project

Useful patterns: `install-64`, package tracking, explicit runtime/GUI ownership, an update-aware path, model-download decisions, and practical performance documentation. Your existing four-model menu should remain your interface; copying its featured-model defaults would remove features.

Do not copy its lifecycle blindly. The runtime archive follows `latest` without a pinned checksum, the GUI checkout is not pinned in this script, and several user/group/systemd commands have no explicit failure guard. The normal uninstall deletes model data, while the current submission guidance says configuration must survive uninstall. The service-state variable is unused and the temporary directory is not consistently used for downloads. Existing accepted scripts are examples, not proof every operation meets today's preferred standard.

## 2. Complete examination: Bambu Studio

Seven files: `install-64`, `uninstall`, `description`, `website`, `credits`, `icon-24.png`, `icon-64.png`.

### Installation flow

The complete installer has two operational lines: register `flatpak` with `install_packages`, then call `flatpak_install com.bambulab.BambuStudio`. Each failure exits nonzero. There is no custom downloader, Python environment, service, model selection, launcher generation, or path selection in the app script; those responsibilities belong to Flatpak and Pi-Apps' helper.

### Uninstall and update

Calls `flatpak_uninstall com.bambulab.BambuStudio`, then `purge_packages`, each guarded by an exit. The app script itself has no special `update` branch and does not manually remove a configuration directory. Detailed data retention belongs to the helper, not these two lines, so it cannot be established solely from this app folder.

### Metadata and assets

The first description line is a short summary; the rest describes the slicer's origins, an xwayland rendering limitation, and GUI/terminal launch instructions. Website links to the publisher's download page. Credits identify Botspot. Icons are valid indexed-color PNGs at 24×24 and 64×64.

### What transfers to your project

Useful patterns: small lifecycle scripts, failure propagation, separate metadata and correctly sized icons. It does not justify turning your project into a Flatpak. No Flatpak build is supplied for your application, and converting it would be a separate functional/distribution project outside CodeLock.

## 3. Complete examination: CloudBuddy

Seven files: `install`, `uninstall`, `description`, `website`, `credits`, `icon-24.png`, `icon-64.png`.

### Installation flow

Registers `yad`, `xclip`, and `expect` through `install_packages`. Deletes an old `~/cloudbuddy` directory with an explicit error guard, clones the repository with `git_clone`, and invokes `~/cloudbuddy/main.sh setup`, also with explicit failure handling. It has a generic `install` file rather than an ARM64-specific file.

### Uninstall and update

Runs `purge_packages`, then removes the application directory and two user-level integration files. There is no update argument handling or separate data-migration step in the supplied script. Its final `rm` exit status becomes the script result. Any setup changes or runtime files beyond those paths require examining the external application; they are not visible in this folder.

### Metadata and assets

Description states what the app does and gives both menu and terminal launch instructions. Website and credits identify the upstream project/maintainer. Icons are valid RGBA PNGs at 24×24 and 64×64.

### What transfers to your project

This is the nearest structural model for a thin adapter around an existing setup script. But your setup also runs apt, changes pip/desktop configuration, asks interactive questions, optionally reboots, and replaces existing data. Calling it from `install-64` would not automatically solve those integration problems. A wrapper needs a deliberate interface and a reliable completion result.

