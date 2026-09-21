#!/usr/bin/env python3
"""Private Pi-Apps receipts and recoverable file transactions; never sources data."""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
import shutil
import sys
import tempfile
import uuid


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def safe_parent(path):
    # Check every existing ancestor before touching a recorded path.
    for parent in (path.parent, *path.parent.parents):
        if parent.is_symlink():
            raise ValueError(f'Symlink ancestor: {parent}')


def signature(path):
    safe_parent(path)
    if path.is_symlink():
        return ['link', os.readlink(path)]
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f'Expected an ordinary file: {path}')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return ['file', digest.hexdigest()]


def inventory(root):
    result = {}
    if root.is_symlink():
        raise ValueError(f'Symlink installation directory: {root}')
    if not root.exists():
        return result
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in list(dirs):
            item = Path(directory) / name
            if item.is_symlink():
                files.append(name)
                dirs.remove(name)
        for name in files:
            item = Path(directory) / name
            result[str(item.relative_to(root))] = signature(item)
    return result


def data_file(name):
    # These locations are user data even when shipped with a default file.
    first = name.split('/')[0]
    return first in {'models', 'outputs', 'extensions', 'embeddings', 'log', 'logs',
                     'config.json', 'ui-config.json', 'styles.csv', 'params.txt',
                     'config_states', 'cache.json', 'webui-user.sh', 'webui-user.bat'}


class Store:
    def __init__(self, directory, home):
        self.directory = Path(directory)
        self.home = Path(home)
        safe_parent(self.directory)
        if self.directory.is_symlink():
            raise ValueError('State directory must not be a symlink')
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.directory.stat().st_uid != os.getuid():
            raise ValueError('State directory belongs to another user')
        self.directory.chmod(0o700)
        self.receipt = self.directory / 'receipt.json'
        self.journal = self.directory / 'transaction.json'
        for path in (self.receipt, self.journal):
            if path.is_symlink():
                raise ValueError(f'Symlink state file: {path}')

    def read(self, path):
        return json.loads(path.read_text()) if path.exists() else None

    def extra_paths(self, root):
        return [root / name for name in ('run_sd.sh', '.sd_gui_runner.sh', '.sd_gui_app.py', '.sd_gui_banner.png')] + [
            self.home / '.local/share/applications/sd-gui.desktop',
            self.home / 'Desktop/StableDiffusionGUI.desktop',
            self.home / '.local/share/icons/hicolor/256x256/apps/sd_icon.png',
            self.home / '.local/share/icons/sd_icon.png']

    def validate(self, record):
        if record['schema'] != 1 or record['uid'] != os.getuid() or record['home'] != str(self.home):
            raise ValueError('Receipt does not belong to this user or schema')
        root = Path(record['root'])
        if not root.is_absolute() or str(root) != os.path.realpath(root) or root == Path('/'):
            raise ValueError('Invalid or redirected installation root')
        allowed = {str(p) for p in self.extra_paths(root)}
        if not set(record.get('extras', {})) <= allowed:
            raise ValueError('Receipt contains an unexpected integration path')
        for group in ('web', 'env'):
            for name in record.get(group, {}):
                p = Path(name)
                if p.is_absolute() or '..' in p.parts:
                    raise ValueError('Invalid relative receipt path')
        return root

    def begin(self, root, stage, manager, token):
        if self.journal.exists():
            self.recover()
        root = Path(os.path.realpath(root))
        if root == Path('/') or not root.is_dir() or root.stat().st_uid != os.getuid():
            raise ValueError('Choose an existing installation directory owned by your user')
        safe_parent(root / 'placeholder')
        old = self.read(self.receipt)
        if old and self.validate(old) != root:
            raise ValueError(f"Pi-Apps already owns an installation at {old['root']}")
        if old and old.get('manager') != manager:
            raise ValueError('The installation belongs to a different Pi-Apps directory')
        web = root / 'stable-diffusion-webui'
        env = root / 'stable-diffusion-env'
        extras = self.extra_paths(root)
        icon_names = {
            self.home / '.local/share/icons/hicolor/256x256/apps/sd_icon.png': 'sd_icon-hicolor.png',
            self.home / '.local/share/icons/sd_icon.png': 'sd_icon-fallback.png',
        }
        legacy_icons = []
        for item in [web, env, *extras]:
            safe_parent(item)
            if item.is_symlink():
                raise ValueError(f'Refusing redirected installation file: {item}')
            if not old and item.exists():
                if item in icon_names and item.is_file() and item.stat().st_uid == os.getuid():
                    legacy_icons.append(item)
                else:
                    raise ValueError(f'Existing unmanaged installation or integration file: {item}. '
                                     'Keep the working installation; shared launchers must be resolved separately.')
        if legacy_icons and root != self.home:
            # A different selected root does not make the default installation obsolete.
            for name in ('stable-diffusion-webui', 'stable-diffusion-env', 'run_sd.sh',
                         '.sd_gui_runner.sh', '.sd_gui_app.py', '.sd_gui_banner.png'):
                item = self.home / name
                if item.exists() or item.is_symlink():
                    raise ValueError(f'Existing default installation may use the shared icons: {item}')
        if old:
            for item in extras:
                expected = old['extras'].get(str(item))
                if signature(item) != expected:
                    raise ValueError(f'Integration file changed outside Pi-Apps: {item}')
        # Refuse to replace files while WebUI, its venv or the GUI is running.
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit() or int(entry.name) == os.getpid():
                continue
            try:
                if entry.stat().st_uid != os.getuid():
                    continue
                args = (entry / 'cmdline').read_bytes().split(b'\0')
                if any(a.decode(errors='replace').startswith((str(env) + '/', str(root / '.sd_gui_app.py'))) for a in args):
                    raise ValueError('Stop Stable Diffusion and close its GUI before updating')
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                pass
        stage_path = Path(stage)
        if stage_path.parent != root or not re.fullmatch(r'\.sd-install-\d+-webui', stage_path.name):
            raise ValueError('Unexpected staging directory')
        if stage_path.exists() or stage_path.is_symlink():
            raise ValueError('Staging path already exists; nothing has been removed')
        backup = root / ('.sd-piapps-backup-' + uuid.uuid4().hex)
        backup.mkdir(mode=0o700)
        snapshots = {}
        for index, item in enumerate(extras):
            snapshots[str(item)] = None
            if item.exists():
                destination = backup / f'extra-{index}'
                shutil.copy2(item, destination)
                snapshots[str(item)] = str(destination)
        record = dict(schema=1, uid=os.getuid(), home=str(self.home), root=str(root),
                      manager=manager, token=token, web={}, env={}, extras={})
        if old and old.get('legacy_icon_backup'):
            record['legacy_icon_backup'] = old['legacy_icon_backup']
        if legacy_icons:
            # Keep these originals outside transaction cleanup and uninstall ownership.
            safe_parent(self.home / 'sd-icon-backup')
            saved_icons = Path(tempfile.mkdtemp(prefix='sd-icon-backup.', dir=self.home))
            for item in legacy_icons:
                shutil.copy2(item, saved_icons / icon_names[item])
            record['legacy_icon_backup'] = str(saved_icons)
        journal = dict(record=record, old=old, backup=str(backup), stage=stage,
                       snapshots=snapshots, moves=[], committed=False)
        write_json(self.journal, journal)
        # Recovery can restore the exact original paths once the journal is durable.
        for item in legacy_icons:
            item.unlink()
        if legacy_icons:
            print(f'Leftover icons backed up to: {record["legacy_icon_backup"]}', flush=True)

    def preserve(self, group, destination):
        journal = self.read(self.journal)
        old = journal['old']
        if not old:
            return
        root = self.validate(old)
        source = root / ('stable-diffusion-webui' if group == 'web' else 'stable-diffusion-env')
        if group == 'env':
            source = Path(journal['backup']) / 'env'
        existing = inventory(source)
        destination = Path(destination)
        for name, sig in existing.items():
            # Keep new versions of unchanged owned code. Preserve everything else.
            if sig == old[group].get(name) and not (group == 'web' and data_file(name)):
                continue
            src, dst = source / name, destination / name
            safe_parent(dst)
            if dst.exists() or dst.is_symlink():
                if signature(dst) == sig:
                    continue
                if not (group == 'web' and data_file(name)):
                    raise ValueError(f'Update would overwrite a modified/untracked file: {src}')
                if dst.is_dir():
                    raise ValueError(f'User data conflicts with a directory: {dst}')
                dst.unlink()
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_symlink():
                dst.symlink_to(os.readlink(src))
            else:
                shutil.copy2(src, dst)

    def capture_web(self, stage):
        journal = self.read(self.journal)
        journal['record']['web'] = {p: sig for p, sig in inventory(Path(stage)).items() if not data_file(p)}
        write_json(self.journal, journal)
        self.preserve('web', stage)

    def activate(self):
        journal = self.read(self.journal)
        root = self.validate(journal['record'])
        for group, name in [('web', 'stable-diffusion-webui'), ('env', 'stable-diffusion-env')]:
            src = root / name
            dst = Path(journal['backup']) / group
            # Journal intent before moving; recovery checks whether the move happened.
            journal['moves'].append([str(src), str(dst), src.exists()])
            write_json(self.journal, journal)
            if src.exists():
                src.rename(dst)
        Path(journal['stage']).rename(root / 'stable-diffusion-webui')

    def commit(self):
        journal = self.read(self.journal)
        record = journal['record']
        root = self.validate(record)
        env = root / 'stable-diffusion-env'
        record['env'] = inventory(env)
        self.preserve('env', env)
        record['extras'] = {str(p): signature(p) for p in self.extra_paths(root) if p.exists()}
        # Only record program files that still match the staged source.
        record['web'] = {p: sig for p, sig in record['web'].items()
                         if signature(root / 'stable-diffusion-webui' / p) == sig}
        write_json(self.receipt, record)
        journal['committed'] = True
        write_json(self.journal, journal)
        self.recover()

    def recover(self):
        journal = self.read(self.journal)
        if not journal:
            return
        root = self.validate(journal['record'])
        backup = Path(journal['backup'])
        stage = Path(journal['stage'])
        if backup.parent != root or not re.fullmatch(r'\.sd-piapps-backup-[a-f0-9]{32}', backup.name):
            raise ValueError('Invalid recovery backup')
        if stage.parent != root or not re.fullmatch(r'\.sd-install-\d+-webui', stage.name):
            raise ValueError('Invalid recovery staging directory')
        if backup.is_symlink() or stage.is_symlink():
            raise ValueError('Recovery directory was redirected')
        allowed_moves = {(str(root / 'stable-diffusion-webui'), str(backup / 'web')),
                         (str(root / 'stable-diffusion-env'), str(backup / 'env'))}
        for original, saved, existed in journal['moves']:
            if (original, saved) not in allowed_moves or not isinstance(existed, bool):
                raise ValueError('Unexpected recovery move')
        for original, snapshot in journal['snapshots'].items():
            if Path(original) not in self.extra_paths(root):
                raise ValueError('Unexpected recovery integration path')
            if snapshot and (Path(snapshot).parent != backup or not re.fullmatch(r'extra-\d+', Path(snapshot).name)):
                raise ValueError('Unexpected integration backup')
        receipt = self.read(self.receipt)
        committed = receipt and receipt.get('token') == journal['record']['token']
        if not committed:
            for original, backup, existed in reversed(journal['moves']):
                src, dst = Path(original), Path(backup)
                safe_parent(src)
                if dst.exists() or not existed:
                    if src.is_symlink():
                        raise ValueError(f'Recovery path became a symlink: {src}')
                    if src.exists():
                        shutil.rmtree(src)
                    if dst.exists():
                        dst.rename(src)
            for original, snapshot in journal['snapshots'].items():
                target = Path(original)
                safe_parent(target)
                if target.is_symlink() or target.is_file():
                    target.unlink()
                if snapshot:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(snapshot, target)
        stage = Path(journal['stage'])
        if stage.exists():
            shutil.rmtree(stage)
        shutil.rmtree(journal['backup'])
        self.journal.unlink()

    def remove(self, manager):
        self.recover()
        record = self.read(self.receipt)
        if not record:
            raise ValueError('No Pi-Apps installation receipt; no files have been guessed or removed')
        root = self.validate(record)
        if record['manager'] != manager:
            raise ValueError('Different Pi-Apps manager owns this installation')
        targets = [(Path(p), sig) for p, sig in record['extras'].items()]
        for group, name in [('web', 'stable-diffusion-webui'), ('env', 'stable-diffusion-env')]:
            base = root / name
            safe_parent(base / 'placeholder')
            targets.extend((base / p, sig) for p, sig in record[group].items())
        # Validate all ancestors before starting a partial removal.
        for path, _ in targets:
            safe_parent(path)
        kept = 0
        for path, expected in targets:
            if path.exists() or path.is_symlink():
                if signature(path) == expected:
                    path.unlink()
                else:
                    kept += 1
        # Empty directories only; never traverse user symlinks or outside the root.
        for name in ('stable-diffusion-webui', 'stable-diffusion-env'):
            for directory, _, _ in os.walk(root / name, topdown=False, followlinks=False):
                try:
                    Path(directory).rmdir()
                except OSError:
                    pass
        print(f'Program files removed. User data remains in {root}; {kept} modified owned files retained.')
        # Keep receipt until dependency removal succeeds so retry remains possible.


def main():
    command, directory, home, *args = sys.argv[1:]
    store = Store(directory, home)
    if command == 'init':
        store.recover()
    elif command == 'root':
        record = store.read(store.receipt)
        if record:
            print(store.validate(record))
    elif command == 'begin':
        store.begin(*args)
    elif command == 'capture-web':
        store.capture_web(*args)
    elif command == 'activate':
        store.activate()
    elif command == 'commit':
        store.commit()
    elif command == 'recover':
        store.recover()
    elif command == 'remove':
        store.remove(*args)
    elif command == 'stop':
        record = store.read(store.receipt)
        root = store.validate(record)
        runner = root / 'run_sd.sh'
        if runner.exists():
            if signature(runner) != record['extras'].get(str(runner)):
                raise ValueError('Launcher was modified; stop the app and restore the owned launcher before removal')
            subprocess.run(['bash', str(runner)], input='3\n', text=True, check=True)
    elif command == 'forget':
        record = store.read(store.receipt)
        store.validate(record)
        record.update(status='removed', web={}, env={}, extras={})
        write_json(store.receipt, record)
    elif command == 'check':
        record = store.read(store.receipt)
        if not record or record['token'] != args[0]:
            raise ValueError('Installer cancelled or did not record a completed installation')
    else:
        raise ValueError('Unknown state operation')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Pi-Apps integration: {error}', file=sys.stderr)
        sys.exit(1)
