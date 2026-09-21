#!/bin/bash
# Sourced only by setup_sd.sh --pi-apps; the standalone installer needs no helper.
[ "${EUID}" -ne 0 ] && [ "$(id -un)" = "$TARGET_USER" ] || { echo 'Run through Pi-Apps as your desktop user.' >&2; exit 1; }
: "${SD_PIAPPS_STATE:?Missing Pi-Apps state directory}" "${SD_PIAPPS_TOKEN:?Missing transaction token}" "${SD_PIAPPS_MANAGER:?Missing Pi-Apps manager}"
SD_PIAPPS_HELPER="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
piapps_state() { /usr/bin/python3 "$SD_PIAPPS_HELPER/state.py" "$1" "$SD_PIAPPS_STATE" "$USER_HOME" "${@:2}"; }
piapps_exit() {
  local result=$?
  trap - EXIT ERR INT TERM
  local child
  while read -r child; do
    [ -z "$child" ] || kill "$child" 2>/dev/null || true
  done < <(jobs -pr)
  wait 2>/dev/null || true
  if ! piapps_state recover; then
    echo 'Recovery failed; retain the transaction and backups for manual recovery.' >&2
    result=1
  fi
  exit "$result"
}
trap piapps_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
piapps_begin() {
  piapps_state begin "$INSTALL_ROOT" "$STAGE_WEBUI_DIR" "$SD_PIAPPS_MANAGER" "$SD_PIAPPS_TOKEN"
}
piapps_packages() {
  # The Pi-Apps API is not nounset-safe. Run it in its own ordinary Bash shell.
  bash "$SD_PIAPPS_HELPER/packages.sh" install "$SD_PIAPPS_MANAGER" "${APT_PACKAGES[@]}"
}
piapps_reboot() {
  sudo -v || { echo 'Installation complete, but reboot authorization failed. Reboot manually.' >&2; return 0; }
  nohup /usr/bin/python3 "$SD_PIAPPS_HELPER/reboot.py" "$SD_PIAPPS_MANAGER_PID" "$SD_PIAPPS_MANAGER_START" \
    "$SD_PIAPPS_MANAGER" "$SD_PIAPPS_STATE" "$SD_PIAPPS_TOKEN" \
    </dev/null >"$SD_PIAPPS_STATE/reboot.log" 2>&1 9>&- &
  disown "$!"
}
