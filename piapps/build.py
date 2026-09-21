#!/usr/bin/env python3
"""Build a Pi-Apps import ZIP from this checkout, without fetching remote code."""
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

project = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1] if len(sys.argv) > 1 else 'Stable-Diffusion-PiApps.zip').resolve()
output.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as temporary:
    app = Path(temporary) / 'Stable Diffusion'
    shutil.copytree(project / 'piapps/app', app)
    payload = app / 'payload'
    payload.mkdir()
    for name in ('setup_sd.sh', 'sd_icon.png', 'sd_gui_banner.png'):
        shutil.copy2(project / name, payload / name)
    (payload / 'piapps').mkdir()
    for name in ('entry.sh', 'hooks.sh', 'packages.sh', 'state.py', 'reboot.py'):
        shutil.copy2(project / 'piapps' / name, payload / 'piapps' / name)
    entries=[]
    for path in sorted(payload.rglob('*')):
        if path.is_file():
            entries.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.relative_to(payload).as_posix())
    (payload / 'SHA256SUMS').write_text('\n'.join(entries)+'\n')
    for name in ('install-64', 'uninstall'):
        (app / name).chmod(0o755)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(app.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(app.parent))
print(output)
