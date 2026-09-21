# Pi-Apps Readiness Review

Reviewed against the supplied project `rpi-automatic1111-main(20260916-221502)(1).zip`, the full reference app ZIP, and upstream Pi-Apps guidance/core. Integration completed 2026-09-17 under the owner's A–E authorization.

**Status: implemented local testing candidate.** This is now an installable app-folder package, rather than metadata with missing lifecycle scripts. It has not been installed on a Raspberry Pi, run through upstream CI, submitted, or accepted. Licensing and model eligibility still need owner decisions.

## Leftover-icon correction — 2026-09-21

The supplied Pi log showed a fresh installation blocked by two regular icon files left behind by standalone removal. The owner confirmed that backing up those icons resolved that obstruction. The package now performs that backup automatically when no installation/launcher conflict exists at the checked paths. Original icon files are retained in a unique `~/sd-icon-backup.*` directory, excluded from uninstall ownership, and restored to their original paths on installation failure. Existing installations, conflicting launchers, and redirected icon paths remain protected. The misleading suggestion to choose another installation location was removed from this conflict error.

The selected root, the default home-root installation paths, and shared launcher paths are checked; other arbitrary installation locations are not searched. No claim is made that every possible custom installation can be discovered. The original installer and its final `[Y/n]` confirmation are unchanged; **Y or Enter** confirms, while **S** is only the main-menu Start key.

Six new unit cases and the mocked full lifecycle cover two/single icons, unique persistent backups, rollback, conflicting installations/launchers, and symlinks. No real Pi installation or inference was performed for this correction. The user's successful manual workaround is not represented as a full release test.

## What changed under A–E

| Scope | Implementation |
| --- | --- |
| A — Dependency tracking | Opt-in Pi-Apps mode calls `install_packages` with the existing package array. `purge_packages` releases dependencies on removal. The Pi-Apps API runs without the standalone script's nounset option. Standalone apt commands and their ordering stay intact. |
| B — Ownership/results | A user-owned private state directory stores JSON receipts and a transaction journal. Completion requires this invocation's transaction token; menu cancellation cannot masquerade as a successful install. Root execution, missing manager context, missing terminal, unmanaged installations, conflicting shortcuts, redirected paths, and concurrent maintenance are rejected. |
| C — Update/removal | Staged source receives retained data before activation. Old WebUI/environment trees and integration files remain available until commit. Recorded move intents cover failure between backup operations. Removal compares recorded hashes before deleting program files. A removal receipt allows reinstall with retained data. GUI/CLI Uninstall delegates to Pi-Apps. |
| D — Scoped settings | Pi-Apps mode skips piwheels-config deletion and global `quick_exec` edits. The existing reboot question remains; an accepted reboot waits for the invoking manager to finish and write a fresh successful status. |
| E — Safe paths | Generated shell assignments use Bash serialization. Desktop Exec fields receive both required escaping layers and invoke the script through `/bin/bash`, which also handles `%` in the script path correctly in GLib. This targeted path fix applies to standalone installs too. |

The canonical installer lives in the project. `piapps/build.py` generates the native package's payload directly from that checkout and adds SHA-256 checks for accidental payload changes. It does not fetch a mutable remote installer. This checksum is integrity checking within the supplied package, not a publisher signature.

The full embedded GUI, original companion artwork, four-model selector, model downloader/progress renderer, platform checks, and input helpers match the uploaded baseline. Menu names, model defaults, dependency pins, runtime mode flags, Stop logic, browser handling, and terminal-closing behavior remain unchanged. GUI/CLI Uninstall changes only for Pi-Apps-owned installations. No broad stylistic refactor was mixed into this integration.

## Data ownership and failure behavior

The receipt is `~/.local/state/rpi-automatic1111/receipt.json`. It records the chosen root, user, owning Pi-Apps directory, transaction token, program-file fingerprints, and integration paths. Receipt values are parsed as JSON, never sourced as shell commands. The state directory is private; normal operations acquire a nonblocking lock.

The preservation inventory includes **all models, outputs, extensions, embeddings, settings and other added files**, not just the four bundled checkpoints. Shipped user-data defaults such as `webui-user.sh` remain data. Symlinks are copied as links and are not recursively followed for ownership/removal. External output locations are not owned. Modified program files survive removal; if a modified or added file conflicts with incoming code during an update, the update aborts and retains the original. Changed integration files also block an update rather than being silently overwritten.

Uninstall removes unchanged receipt-owned source, environment, launchers and icons, then releases package dependencies. Empty program directories are pruned. Runtime-created files and modified files may remain, including parts of an environment; users can inspect those leftovers themselves. An empty runtime directory and the small state/removal record can remain. This is deliberate data preservation, not a claim that removal leaves the home directory empty.

Fresh-install failure removes the attempted program trees and restores prior integration state. Update failure restores backed-up trees and launchers. The next Pi-Apps operation recovers a journal left by an interrupted process. Recovery was tested at backup-move boundaries. It is **not a power-loss durability guarantee**: filesystem, storage and sudden-power-failure behavior have not been tested on a Pi. Keep independent backups.

Do not run standalone setup over a Pi-Apps installation. Standalone reinstall and uninstall retain their existing destructive behavior. The adapter does not claim to make that separate workflow data-preserving.

## Validation performed

- 23 unit/regression tests (including the 2026-09-21 leftover-icon regression cases): fresh/update rollback, move-intent interruption, unmanaged-file rejection, ownership/path validation, modified/untracked data retention, external symlink retention, shell serialization, actual GLib desktop launch parsing, reboot status/token/timeout gating, and baseline fingerprints.
- A lifecycle harness exercised the actual menu, helper, receipt and launcher-generation code: cancel; fresh install; injected pip failure and rollback; update-uninstall handoff; successful update; removal; reinstall with retained data; accepted deferred reboot. Downloads/package installation were mocked. The copied fixture replaces the platform check and root guard because this container exposes only UID 0; those replacements are not shipped in the app payload. No package installation or real reboot ran.
- All 16 combinations of the four model flags produced identical menu rows, totals and selected-model labels against the supplied baseline. Download progress output matched at terminal widths 2, 20, 40, 60, 80 and 120.
- Bash syntax, embedded GUI Python syntax, bundle checks and Python compilation passed. The new adapters pass ShellCheck. Existing standalone diagnostics remain: quoted tilde-pattern advice, overlapping Pi model patterns, unused OS-version variable, and external-source notices. No new standalone diagnostic class was introduced. These were not “fixed” by changing locked behavior.
- The GUI template, ten locked functions and both original artwork files match baseline fingerprints. This is evidence about those components, not proof of identical behavior on every desktop or OS.

Run the included checks from the project directory:

```bash
bash validate_bundle.sh
python3 -m unittest discover -s tests -v
python3 tests/verify_model_ui.py tests/model-baseline.txt setup_sd.sh
python3 tests/integration.py
```

The lifecycle harness is for an isolated Linux test environment; it deliberately mocks system operations. The GLib test needs `libgio-2.0`. No test substitutes for an actual ARM64 install and image-generation session.

## Remaining submission concerns

| Severity | Concern | Recommendation / boundary |
| --- | --- | --- |
| Blocker | No project license and no recorded artwork redistribution grant. | Owner chooses the code license and confirms rights to both assets. No license was invented or applied. |
| Blocker | Default model terms and all-ages suitability are unresolved. | Review all four publishers' terms and intended content with Pi-Apps maintainers. Model choices/defaults remain locked. |
| High | No real Pi installation, inference, GUI-session or upstream CI results. | Test on a disposable supported Pi OS image; record board, RAM, OS, Python, package versions and actual results. Do not test first on the working installation. |
| High | Pi-Apps core purges dependency registrations after a failed install, including some cancelled/failed updates. File rollback cannot prevent that external action. | Retry through Pi-Apps to restore package registration/dependencies. Discuss dependency preservation on failed updates with maintainers; the adapter does not falsify success or edit manager state to bypass it. |
| High | Existing interactive menus need a controlling terminal; unattended CI currently fails explicitly. | Run lifecycle tests in a PTY. Agree on any unattended-install interface separately; silent defaults or synthetic menu input are not shipped in the installer. |
| High | Several dependencies are unpinned; model hashes come from live upstream headers rather than a release-owned manifest. | Capture and validate reproducible ARM64 dependency/model revisions for a release. Existing working pins and downloads were kept. |
| Medium | Rollback needs space for old and new trees, including copied model data. There is no disk-space preflight. | Measure requirements on a supported Pi; add a preflight only with a separately agreed policy. The preservation copy can be slow. |
| Medium | Strict RAM check uses reported 4 GiB, potentially rejecting nominal 4 GB boards; OS gate accepts more combinations than have been tested. | Establish a real support matrix before advertising compatibility or changing the gate. |
| Medium | LAN and Offline modes both listen on the network without configured authentication. | Document trusted-network use. Do not describe Offline as network isolation; runtime flags were not changed. |
| Medium | Skipping global `quick_exec` settings may leave a desktop trust/execute prompt. | Test application-menu and desktop launch under the supported desktop sessions. Trust the individual shortcut using the desktop's UI rather than changing global policy. |
| Medium | Existing GUI/uninstall text says “all files,” while Pi-Apps mode retains data. | README and app metadata explain the distinction. A mode-aware text adjustment would make this clearer, but wording/style changes were left outside A–E. |
| Medium | Self-contained app payload is larger than a typical thin Pi-Apps script. | This is intentional for a reviewable local import with no unpublished URL. Before upstream submission, agree whether to use a pinned, checksummed release asset. Do not replace it with an unverified `main` download. |
| Low | Existing standalone ShellCheck findings and literal `~/Desktop` assumption. | Review separately under CodeLock after real desktop tests. |

## Before submitting

1. Resolve the license, artwork and model eligibility decisions.
2. Test clean install, each model, no-model mode, GUI on/off, both shortcuts, custom paths, first LAN launch, an actual image, Offline mode, Stop, browser close, terminal behavior and both reboot answers.
3. Test update/cancellation/failure and uninstall with valuable-looking fixture data in models, outputs, extensions, settings, outside output paths and modified files. Confirm actual Pi-Apps package/status behavior, including the failure limitation above.
4. Run the project's tests and the supported Pi-Apps contribution workflow on a fork. Include honest results and remaining limitations in the submission.

The reference comparison in `Pi-Apps-Reference-Apps.md` contains full examinations of Ollama GUI, Bambu Studio and CloudBuddy. Their accepted scripts illustrate conventions; they are not blanket exemptions from current submission requirements.

Sources: [Pi-Apps app creation/submission guide](https://pi-apps.io/wiki/development/Creating-an-app/), [contribution guide](https://github.com/Botspot/pi-apps/blob/master/CONTRIBUTING.md), [manager lifecycle](https://github.com/Botspot/pi-apps/blob/master/manage), [package API](https://github.com/Botspot/pi-apps/blob/master/api), and [Desktop Entry Exec specification](https://specifications.freedesktop.org/desktop-entry/latest/exec-variables.html). Upstream behavior and requirements can change; this review describes the inspected snapshot.
