#!/usr/bin/env python3
"""Wait for the exact manager process to finish before honoring its reboot."""
import json
from pathlib import Path
import subprocess
import sys
import time

pid, started, manager, state, token = sys.argv[1:]
for _ in range(300):
    try:
        fields = Path('/proc', pid, 'stat').read_text().rsplit(')', 1)[1].split()
        running = fields[0] != 'Z' and fields[19] == started
    except FileNotFoundError:
        running = False
    if not running:
        break
    time.sleep(1)
else:
    sys.exit('Manager did not finish within five minutes; reboot manually.')
receipt = json.loads(Path(state, 'receipt.json').read_text())
status = Path(manager, 'data/status/Stable Diffusion').read_text().strip()
if (receipt.get('token') != token or status != 'installed' or
        Path(manager, 'data/status/Stable Diffusion').stat().st_mtime_ns <
        Path(state, 'receipt.json').stat().st_mtime_ns):
    sys.exit('Pi-Apps did not confirm this installation; reboot cancelled.')
subprocess.run(['sudo', '-n', 'reboot'], check=True)
