#!/bin/bash
set -euo pipefail
mode=$1
SD_PIAPPS_MANAGER=$2
SD_PIAPPS_INPUT=${3:-}
SD_PIAPPS_MANAGER=$(realpath -- "$SD_PIAPPS_MANAGER")
HELPER=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[ "$EUID" -ne 0 ] || { echo 'Run Pi-Apps as your desktop user, not root.' >&2; exit 1; }
[ -f "$SD_PIAPPS_MANAGER/api" ] && [ -x "$SD_PIAPPS_MANAGER/manage" ] || { echo 'Pi-Apps API/manager missing.' >&2; exit 1; }
USER_HOME=$(getent passwd "$(id -u)" | cut -d: -f6)
[ "$HOME" = "$USER_HOME" ] || { echo 'HOME must belong to the current user.' >&2; exit 1; }
# Locate the invoking manager, including shells inserted by nice/terminal launchers.
read -r SD_PIAPPS_MANAGER_PID SD_PIAPPS_MANAGER_START < <(/usr/bin/python3 - "$SD_PIAPPS_MANAGER/manage" <<'PY'
import os
from pathlib import Path
import sys
pid = os.getppid()
while pid > 1:
    proc = Path('/proc', str(pid))
    fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    args = (proc / 'cmdline').read_bytes().split(b'\0')
    if os.fsencode(sys.argv[1]) in args:
        print(pid, fields[19])
        break
    pid = int(fields[1])
else:
    sys.exit('Launch this app through the Pi-Apps manager.')
PY
)
SD_PIAPPS_STATE="$USER_HOME/.local/state/rpi-automatic1111"
state() { /usr/bin/python3 "$HELPER/state.py" "$1" "$SD_PIAPPS_STATE" "$USER_HOME" "${@:2}"; }
# Validate state parents before opening the lock file. Recovery runs under the lock.
/usr/bin/python3 - "$HELPER" "$SD_PIAPPS_STATE" "$USER_HOME" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from state import Store
store = Store(sys.argv[2], sys.argv[3])
lock = store.directory / 'lock'
if lock.is_symlink():
    sys.exit('Refusing symlink lock file')
PY
exec 9>"$SD_PIAPPS_STATE/lock"
flock -n 9 || { echo 'Another Stable Diffusion maintenance operation is running.' >&2; exit 1; }
state init
export SD_PIAPPS_MANAGER SD_PIAPPS_INPUT SD_PIAPPS_STATE SD_PIAPPS_MANAGER_PID SD_PIAPPS_MANAGER_START
case "$mode" in
  install)
    if ! (exec 8<>/dev/tty) 2>/dev/null; then
      echo 'This installer needs a controlling terminal for its existing menus. Run Pi-Apps in a terminal.' >&2
      exit 1
    fi
    SD_PIAPPS_TOKEN=$(/usr/bin/python3 -c 'import uuid; print(uuid.uuid4().hex)')
    export SD_PIAPPS_TOKEN
    bash "$HELPER/../setup_sd.sh" --pi-apps
    state check "$SD_PIAPPS_TOKEN"
    ;;
  uninstall)
    # Pi-Apps updates uninstall first. The installer replaces the owned files transactionally.
    [ "$SD_PIAPPS_INPUT" != update ] || exit 0
    root=$(state root)
    if [ -z "$root" ]; then
      echo 'No owned files recorded; leaving existing files alone.'
      bash "$HELPER/packages.sh" purge "$SD_PIAPPS_MANAGER"
      exit 0
    fi
    state stop
    state remove "$SD_PIAPPS_MANAGER"
    bash "$HELPER/packages.sh" purge "$SD_PIAPPS_MANAGER"
    state forget
    ;;
  *) exit 1 ;;
esac
