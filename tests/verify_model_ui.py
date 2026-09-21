#!/usr/bin/env python3
"""Isolated four-model selector and progress-renderer checks; no downloads.
Usage: python3 verify_model_ui.py BASELINE/setup_sd.sh POLISHED/setup_sd.sh
"""
import errno
import fcntl
import itertools
import os
from pathlib import Path
import pty
import re
import select
import signal
import struct
import subprocess
import sys
import termios
import time


def function(source, name):
    return re.search(r'^' + name + r'\(\) \{\n.*?^\}', source, re.M | re.S).group()


def run_terminal(script, width=80):
    pid, fd = pty.fork()
    if pid == 0:
        fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack('HHHH', 24, width, 0, 0))
        os.execvp('bash', ['bash', '-c', script])
    output = b''
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if select.select([fd], [], [], 0.1)[0]:
                try:
                    data = os.read(fd, 65536)
                    if not data:
                        break
                    output += data
                except OSError as exc:
                    if exc.errno == errno.EIO:
                        break
                    raise
        else:
            raise TimeoutError('Isolated function stalled')
        _, status = os.waitpid(pid, 0)
        pid = None
        assert os.waitstatus_to_exitcode(status) == 0, output
        return output
    finally:
        os.close(fd)
        if pid is not None:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)


sources = [Path(p).read_text() for p in sys.argv[1:]]
assert len(sources) == 2
flags = ['DOWNLOAD_CYBERREALISTIC', 'DOWNLOAD_REALISTIC_VISION', 'DOWNLOAD_REALISTIC_VISION_V6', 'DOWNLOAD_REAL_DREAM']
names = ['CyberRealistic_V7.0_FP16.safetensors', 'Realistic_Vision_V5.1-inpainting.safetensors', 'Realistic_Vision_V6.0_NV_B1_fp16.safetensors', 'sd1.5-real-dream-16.safetensors']
for selection in itertools.product((0, 1), repeat=4):
    total = sum(a * b for a, b in zip(selection, (213, 427, 213, 213)))
    results = []
    for source in sources:
        definitions = '\n'.join(f'{name}={value}' for name, value in zip(flags, selection))
        # The stub supplies only Q after rendering: no install path is reached.
        script = definitions + '\nclear() { :; }\nread() { key=q; }\n' + function(source, 'select_models') + '\nselect_models'
        out = run_terminal(script).decode()
        assert f'Total selected download: {total // 100}.{total % 100:02d} GB (approx.)' in out
        for chosen, name in zip(selection, names):
            assert f'[{"X" if chosen else " "}] {name}' in out
        label = subprocess.check_output(['bash', '-c', definitions + '\nDOWNLOAD_MODELS=1\n' + function(source, 'selected_models_label') + '\nselected_models_label'], text=True)
        for chosen, name in zip(selection, names):
            assert (name in label) == bool(chosen)
        results.append((out, label))
    assert results[0] == results[1]
print('PASS: all 16 model selections have identical rows, approximate totals, and summary labels')
for width in (2, 20, 40, 60, 80, 120):
    results = []
    for source in sources:
        out = run_terminal(function(source, 'render_model_progress') + '\nrender_model_progress 76 "123.45 MB/s" 100 100 80 60 40', width)
        assert out.startswith(b'\x1b[1G\x1b[2K'), out
        visible = out[len(b'\x1b[1G\x1b[2K'):]
        assert b'\n' not in visible and b'\r' not in visible
        assert len(visible) < width, (width, visible)
        results.append(out)
    assert results[0] == results[1]
print('PASS: progress output identical and shorter than terminal width at 2, 20, 40, 60, 80, 120 columns')
for source in sources:
    gui = re.search(r"cat <<'EOF' > \"\$INSTALL_ROOT/\.sd_gui_app\.py\"\n(.*?)\nEOF", source, re.S).group(1)
    assert 'Press ENTER to close' not in gui
    assert '"--command", f"bash -c {shell_quote(cmd)}"' in gui
print('PASS: no Enter-to-close prompt in either GUI template')
print('Limits: isolated functions and static GUI check; no network, install, inference, or desktop session.')
