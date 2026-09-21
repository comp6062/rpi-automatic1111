# Changes for the approved Pi-Apps integration

Baseline: `rpi-automatic1111-main(20260916-221502)(1).zip`.

## Technical changes — authorized A–E

- Added opt-in `setup_sd.sh --pi-apps` hooks and native `install-64`/`uninstall` entry points. Normal standalone invocation still needs only `setup_sd.sh`.
- Registered apt dependencies with Pi-Apps in that mode; kept standalone apt behavior.
- Added JSON ownership/completion records, a maintenance lock, conflict checks, retained-data handling, backup journals, failure recovery, and removal through the manager.
- Skipped global pip/file-manager settings changes in Pi-Apps mode. Deferred accepted reboot requests until manager success.
- Fixed shell and desktop path serialization, including `%` in script paths. Desktop entries explicitly invoke `/bin/bash` for the existing Bash launchers. This is the approved standalone-visible technical change.
- Added a builder that generates the Pi-Apps import ZIP from the canonical source, rather than keeping a separate edited installer.
- Updated the bundle validator for the safely serialized runtime-directory assignment. Release ZIPs record executable permissions.

## Documentation and presentation

- Kept the README's badges, numbered organization, existing model descriptions, and stacked model layout for narrow windows.
- Distinguished standalone removal/reinstall behavior from Pi-Apps data retention and added import/build instructions.
- Added the readiness review, source comparisons for three reference apps, and reproducible test instructions.
- Reused the original artwork; native package icons are 24/64-pixel derivatives prepared from the supplied icon.

## Preserved under CodeLock

Four model options/defaults, selection keys and totals, downloads and progress rendering, installation menu, existing prompts, GUI source/styling, artwork, runtime LAN/Offline/Stop behavior, browser handling, terminal behavior, dependency pins, installed filenames and selected-root workflow. The GUI/CLI Uninstall action uses Pi-Apps only when the installation was created through that integration.

## Evidence and limits

See `Pi-Apps-Readiness-Review.md` for tests and unresolved risks. Local unit, GLib path and mocked lifecycle checks passed. Actual Raspberry Pi installation, model downloads, inference, desktop interaction and Pi-Apps CI have not run here. Neither licensing nor upstream acceptance is implied. Nothing was published or submitted.


## 2026-09-21 — leftover icons no longer block a fresh Pi-Apps install

The Pi-Apps state helper now backs up the two old icon files when they are the only conflicting artifacts at the checked paths. Backups use a unique `~/sd-icon-backup.*` directory, survive uninstall, and support restoration if installation fails. Existing installations and launchers still block adoption; symlinked or differently owned icons are rejected. The selected/default roots and shared launchers are checked without scanning the home directory for arbitrary custom installations.

Both release ZIPs were rebuilt from the same canonical source and documentation updated. The main `setup_sd.sh`, prompts, models, GUI, runtime controls, and standalone workflow were not edited for this correction. Added six regression tests and extended the mocked lifecycle to reproduce the reported icon-only condition and a failed fresh installation.
