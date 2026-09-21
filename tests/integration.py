#!/usr/bin/env python3
"""Exercise real menus/hooks/launch generation with fake network, apt and pip.
Runs in the single-UID container with mocked system commands; no system changes.
Only validate_platform and root guards are replaced in the copied fixture.
The unmodified root guard is checked separately. Never used in builds.
"""
import errno
import json
import os
from pathlib import Path
import pty
import pwd
import re
import select
import shutil
import subprocess
import tempfile
import time
import zipfile

project=Path(__file__).resolve().parents[1]
base=Path(tempfile.mkdtemp(prefix='sd-integration-'))
base.chmod(0o755)
home=base/'home';home.mkdir()
manager=home/'pi-apps'; manager.mkdir()
mock=base/'bin'; mock.mkdir()
log=home/'commands.log'
user=pwd.getpwuid(os.getuid())

def script(path, body):
    path.write_text('#!/bin/bash\n'+body+'\n'); path.chmod(0o755)

try:
    output=base/'app.zip'
    subprocess.run(['python3',str(project/'piapps/build.py'),str(output)],check=True,stdout=subprocess.DEVNULL)
    with zipfile.ZipFile(output) as z: z.extractall(manager/'apps')
    app=manager/'apps/Stable Diffusion'
    source=app/'payload/setup_sd.sh'
    text=source.read_text()
    text=re.sub(r'^validate_platform\(\) \{\n.*?^\}', 'validate_platform() { :; }', text, flags=re.M|re.S)
    source.write_text(text)
    for name in ('entry.sh','hooks.sh'):
        helper=app/'payload/piapps'/name
        content=helper.read_text()
        content=content.replace('[ "$EUID" -ne 0 ]', '[ 1 = 1 ]').replace('[ "${EUID}" -ne 0 ]','[ 1 = 1 ]')
        helper.write_text(content)
    # Bypass only the distribution checksum after explicitly modifying the test fixture.
    script(app/'install-64','exec bash "$(dirname "$0")/payload/piapps/entry.sh" install "'+str(manager)+'" "${1:-}"')
    (app/'uninstall').chmod(0o755)
    script(manager/'manage', '''mkdir -p "$HOME/pi-apps/data/status"
if [ "$1" = install ]; then script=install-64; else script=uninstall; fi
bash "$HOME/pi-apps/apps/Stable Diffusion/$script" "${3:-}"
result=$?
if [ "$result" = 0 ]; then printf '%sed\\n' "$1" > "$HOME/pi-apps/data/status/Stable Diffusion"; fi
exit "$result"''')
    (manager/'api').write_text('install_packages() { printf "install_packages %s\\n" "$*" >> "$HOME/commands.log"; }; purge_packages() { echo purge_packages >> "$HOME/commands.log"; }\n')
    script(mock/'getent','printf "root:x:0:0::%s:/bin/bash\\n" "$HOME"')
    script(mock/'sudo','''echo "sudo $*" >> "$HOME/commands.log"
if [ "$1" = -u ]; then shift 2; fi
case "$1" in apt|sed|reboot) exit 90;; -v) exit 0;; esac
exec "$@"''')
    script(mock/'git','''case "$1" in
clone) dest=${@: -1}; mkdir -p "$dest/modules"; echo 'code' > "$dest/launch.py"; echo '# requirements' > "$dest/requirements.txt"; echo '# code' > "$dest/modules/launch_utils.py";;
checkout) :;; rev-parse) echo 82a973c04367123ae98bd9abdf80d9eda9b910e2;; *) exit 91;; esac''')
    script(mock/'python3','''if [ "${1:-}" = -m ] && [ "${2:-}" = venv ]; then
  mkdir -p "$3/bin"
  echo 'deactivate() { :; }' > "$3/bin/activate"
  ln -s /usr/bin/python3 "$3/bin/python"
else exec /usr/bin/python3 "$@"; fi''')
    script(mock/'python','''if [ -f "$HOME/fail-pip" ]; then exit 42; fi
cat >/dev/null </dev/null
exit 0''')
    script(mock/'sleep',':')
    script(mock/'sync',':')
    script(mock/'gtk-update-icon-cache',':')
    for path in [home, *home.rglob('*')]: os.chown(path,user.pw_uid,user.pw_gid)
    # Parent creates fixture data as needed; keep ownership consistent.
    def owned(path,text):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        for p in [path,*path.parents]:
            if p==home.parent: break
            os.chown(p,user.pw_uid,user.pw_gid)
    owned(home/'.config/pip/pip.conf','piwheels untouched\n')
    owned(home/'.config/libfm/libfm.conf','[config]\nquick_exec=0\n')
    def run(action, keys='', update=False):
        pid,fd=pty.fork()
        if pid==0:
            os.setgid(user.pw_gid);os.setuid(user.pw_uid)
            os.chdir(home)
            env=dict(os.environ,HOME=str(home),PATH=str(mock)+':/usr/bin:/bin',TERM='xterm')
            os.execve(str(manager/'manage'),[str(manager/'manage'),action,'Stable Diffusion']+(['update'] if update else []),env)
        data=b'';sent=False;start=time.monotonic();result=0
        while time.monotonic()-start<30:
            if select.select([fd],[],[],.1)[0]:
                try: chunk=os.read(fd,65536)
                except OSError as e:
                    if e.errno==errno.EIO:break
                    raise
                if not chunk:break
                data+=chunk
                if keys and not sent and b'Q) Quit' in data:
                    os.write(fd,keys.encode());sent=True
            result,status=os.waitpid(pid,os.WNOHANG)
            if result: break
        else:
            os.kill(pid,9);raise AssertionError('Timed out: '+data.decode(errors='replace')[-4000:])
        if not result: _,status=os.waitpid(pid,0)
        os.close(fd)
        (base/(action+str(time.time_ns())+'.log')).write_bytes(data)
        return os.waitstatus_to_exitcode(status),data.decode(errors='replace')
    code,out=run('install','q');assert code!=0,out
    assert not (home/'.local/state/rpi-automatic1111/receipt.json').exists()
    code,out=run('uninstall');assert code==0,out
    legacy_paths = [home/'.local/share/icons/hicolor/256x256/apps/sd_icon.png',
                    home/'.local/share/icons/sd_icon.png']
    for i, icon in enumerate(legacy_paths): owned(icon, f'legacy icon {i}')
    owned(home/'fail-pip', 'fail fresh installation')
    code,out=run('install','1syn');assert code!=0,out
    for i, icon in enumerate(legacy_paths): assert icon.read_text()==f'legacy icon {i}'
    (home/'fail-pip').unlink()
    code,out=run('install','1syn');assert code==0,out[-5000:]
    receipt=home/'.local/state/rpi-automatic1111/receipt.json'
    first=json.loads(receipt.read_text())['token']
    saved_icons=Path(json.loads(receipt.read_text())['legacy_icon_backup'])
    assert (saved_icons/'sd_icon-hicolor.png').read_text()=='legacy icon 0'
    assert (saved_icons/'sd_icon-fallback.png').read_text()=='legacy icon 1'
    print('PASS: stale icons backed up automatically; failed fresh install restores both originals')
    assert (home/'.config/pip/pip.conf').read_text()=='piwheels untouched\n'
    assert 'quick_exec=0' in (home/'.config/libfm/libfm.conf').read_text()
    owned(home/'stable-diffusion-webui/models/custom.safetensors','user model')
    owned(home/'stable-diffusion-webui/outputs/image.png','user output')
    owned(home/'fail-pip','fail')
    code,out=run('install','1syn',True);assert code!=0,out
    assert json.loads(receipt.read_text())['token']==first
    assert (home/'run_sd.sh').exists()
    assert (home/'stable-diffusion-webui/models/custom.safetensors').read_text()=='user model'
    (home/'fail-pip').unlink()
    code,out=run('uninstall',update=True);assert code==0,out
    assert (home/'run_sd.sh').exists()
    code,out=run('install','1syn',True);assert code==0,out[-5000:]
    assert json.loads(receipt.read_text())['token']!=first
    code,out=run('uninstall');assert code==0,out
    assert not (home/'run_sd.sh').exists()
    assert (home/'stable-diffusion-webui/outputs/image.png').read_text()=='user output'
    assert 'purge_packages' in log.read_text()
    code,out=run('install','1syy');assert code==0,out[-5000:]
    assert (home/'stable-diffusion-webui/models/custom.safetensors').read_text()=='user model'
    for _ in range(40):
        if 'sudo -n reboot' in log.read_text(): break
        time.sleep(.1)
    assert 'sudo -n reboot' in log.read_text(), 'Deferred reboot worker did not survive installer exit'
    assert (manager/'data/status/Stable Diffusion').read_text().strip()=='installed'
    print('PASS: accepted reboot survives installer exit and waits for manager success (sudo mocked)')
    print('PASS: real menus: cancel, empty uninstall, fresh install, pip failure rollback, update, uninstall, reinstall with retained data')
    print('PASS: Pi-Apps package dispatch, receipt/status, unchanged pip/file-manager settings, generated GUI and launchers')
    print('LIMIT: fake platform, git, apt, pip; no ARM64/inference/desktop-session validation')
finally:
    shutil.rmtree(base)
