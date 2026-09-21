import importlib.util
from pathlib import Path
import tempfile
import unittest
import sys

MODULE = Path(__file__).resolve().parents[1] / 'piapps/state.py'
spec = importlib.util.spec_from_file_location('state', MODULE)
state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state)

class Transactions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.root = self.home / 'space "quote" $HOME `echo` % directory'
        self.root.mkdir()
        self.store = state.Store(self.home / 'state', self.home)
        self.stage = self.root / '.sd-install-123-webui'
        self.web = self.root / 'stable-diffusion-webui'
        self.env = self.root / 'stable-diffusion-env'
        self.manager = str(self.home / 'pi-apps')
    def tearDown(self):
        self.temp.cleanup()
    def file(self, path, text='data'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    def start(self, token='first'):
        self.store.begin(str(self.root), str(self.stage), self.manager, token)
        self.file(self.stage / 'launch.py', 'code')
        self.file(self.stage / 'webui-user.sh', 'default')
        self.store.capture_web(str(self.stage))
    def install(self):
        self.start()
        self.store.activate()
        self.file(self.env / 'bin/python', 'venv')
        self.file(self.root / 'run_sd.sh', 'launcher')
        self.store.commit()
    def test_uninstall_preserves_all_nonowned_and_modified(self):
        self.install()
        for name in ['models/m.safetensors','outputs/p.png','extensions/x/code.py','config.json','custom.bin']:
            self.file(self.web / name)
        self.file(self.web / 'launch.py', 'user edit')
        self.file(self.env / 'custom.txt')
        self.store.remove(self.manager)
        for name in ['models/m.safetensors','outputs/p.png','extensions/x/code.py','config.json','custom.bin','launch.py','webui-user.sh']:
            self.assertTrue((self.web/name).exists(), name)
        self.assertFalse((self.env/'bin/python').exists())
        self.assertTrue((self.env/'custom.txt').exists())
        self.assertFalse((self.root/'run_sd.sh').exists())
    def test_update_preserves_data_and_external_link(self):
        self.install()
        self.file(self.web/'models/custom')
        self.file(self.web/'config.json', '{"user":true}')
        outside=self.home/'outside'; outside.mkdir()
        self.file(outside/'photo')
        (self.web/'outputs').symlink_to(outside)
        self.start('second')
        self.assertTrue((self.stage/'outputs').is_symlink())
        self.store.activate()
        self.file(self.env/'bin/python', 'new venv')
        self.file(self.root/'run_sd.sh', 'new launcher')
        self.store.commit()
        self.assertEqual((self.web/'config.json').read_text(), '{"user":true}')
        self.store.remove(self.manager)
        self.assertTrue((outside/'photo').exists())
        self.assertTrue((self.web/'models/custom').exists())
    def test_failure_restores_trees_and_launchers(self):
        self.install()
        self.file(self.web/'models/custom')
        self.start('second')
        self.store.activate()
        self.file(self.env/'bin/python', 'broken')
        self.file(self.root/'run_sd.sh', 'broken')
        self.store.recover()
        self.assertEqual((self.env/'bin/python').read_text(),'venv')
        self.assertEqual((self.root/'run_sd.sh').read_text(),'launcher')
        self.assertTrue((self.web/'models/custom').exists())
        self.assertEqual(self.store.read(self.store.receipt)['token'],'first')
    def test_failure_between_backup_moves(self):
        self.install(); self.start('second')
        journal=self.store.read(self.store.journal)
        backup=Path(journal['backup'])/'web'
        journal['moves'].append([str(self.web), str(backup), True])
        state.write_json(self.store.journal,journal)
        self.web.rename(backup)
        self.store.recover()
        self.assertTrue((self.web/'launch.py').exists())
        self.assertEqual((self.env/'bin/python').read_text(),'venv')
    def test_intent_written_move_not_done(self):
        self.install(); self.start('second')
        journal=self.store.read(self.store.journal)
        journal['moves'].append([str(self.web),str(Path(journal['backup'])/'web'),True])
        state.write_json(self.store.journal,journal)
        self.store.recover()
        self.assertTrue((self.web/'launch.py').exists())
    def test_fresh_failure_removes_only_attempt(self):
        self.start(); self.store.activate()
        self.file(self.root/'unrelated')
        self.file(self.root/'run_sd.sh')
        self.file(self.env/'bin/python')
        self.store.recover()
        self.assertFalse(self.web.exists()); self.assertFalse(self.env.exists())
        self.assertFalse((self.root/'run_sd.sh').exists())
        self.assertTrue((self.root/'unrelated').exists())
    def test_unmanaged_collision(self):
        self.file(self.root/'run_sd.sh')
        with self.assertRaises(ValueError): self.start()
        self.assertEqual((self.root/'run_sd.sh').read_text(),'data')
    def test_modified_program_blocks_update_without_loss(self):
        self.install(); self.file(self.web/'launch.py','custom code')
        with self.assertRaises(ValueError): self.start('second')
        self.store.recover()
        self.assertEqual((self.web/'launch.py').read_text(),'custom code')
    def test_redirected_parent_blocks_uninstall(self):
        self.install()
        outside=self.home/'outside'; self.env.rename(outside)
        self.env.symlink_to(outside)
        with self.assertRaises(ValueError): self.store.remove(self.manager)
        self.assertTrue((outside/'bin/python').exists())
    def test_receipt_paths_cannot_escape(self):
        self.install()
        record=self.store.read(self.store.receipt)
        record['web']['../../outside']=['file','x']
        state.write_json(self.store.receipt,record)
        with self.assertRaises(ValueError): self.store.remove(self.manager)
    def test_wrong_root_and_manager_rejected(self):
        self.install()
        with self.assertRaises(ValueError): self.store.remove('/other')
        with self.assertRaises(ValueError): self.store.begin(str(self.home),str(self.stage),self.manager,'next')


    def legacy_icons(self):
        icons = self.store.extra_paths(self.root)[-2:]
        for i, icon in enumerate(icons):
            self.file(icon, f'original icon {i}')
        return icons

    def test_legacy_icons_backup_survives_commit_and_uninstall(self):
        icons = self.legacy_icons()
        self.start()
        journal = self.store.read(self.store.journal)
        backup = Path(journal['record']['legacy_icon_backup'])
        self.assertTrue(all(not p.exists() for p in icons))
        self.store.activate()
        self.file(self.env / 'bin/python')
        for icon in icons:
            self.file(icon, 'new icon')
        self.store.commit()
        self.store.remove(self.manager)
        self.assertEqual((backup / 'sd_icon-hicolor.png').read_text(), 'original icon 0')
        self.assertEqual((backup / 'sd_icon-fallback.png').read_text(), 'original icon 1')
        self.assertTrue(all(not p.exists() for p in icons))

    def test_legacy_icons_restored_on_failure(self):
        icons = self.legacy_icons()
        self.start()
        for icon in icons:
            self.file(icon, 'partially installed icon')
        self.store.recover()
        for i, icon in enumerate(icons):
            self.assertEqual(icon.read_text(), f'original icon {i}')

    def test_single_leftover_icon_and_unique_backup(self):
        icon = self.store.extra_paths(self.root)[-1]
        self.file(icon, 'one icon')
        self.start()
        first = self.store.read(self.store.journal)['record']['legacy_icon_backup']
        self.store.recover()
        self.start()
        second = self.store.read(self.store.journal)['record']['legacy_icon_backup']
        self.assertNotEqual(first, second)
        self.assertEqual((Path(first) / 'sd_icon-fallback.png').read_text(), 'one icon')
        self.store.recover()

    def test_legacy_icons_do_not_bypass_launcher_conflict(self):
        icons = self.legacy_icons()
        self.file(self.home / '.local/share/applications/sd-gui.desktop', 'existing launcher')
        with self.assertRaises(ValueError):
            self.start()
        self.assertTrue(all(p.exists() for p in icons))
        self.assertFalse(list(self.home.glob('sd-icon-backup.*')))

    def test_legacy_icons_do_not_bypass_other_default_installation(self):
        icons = self.legacy_icons()
        self.file(self.home / 'run_sd.sh', 'working installation')
        with self.assertRaises(ValueError):
            self.start()
        self.assertTrue(all(p.exists() for p in icons))

    def test_legacy_icon_symlink_rejected(self):
        icons = self.legacy_icons()
        icons[0].unlink()
        outside = self.home / 'unrelated.png'
        self.file(outside, 'unrelated')
        icons[0].symlink_to(outside)
        with self.assertRaises(ValueError):
            self.start()
        self.assertEqual(outside.read_text(), 'unrelated')

if __name__=='__main__': unittest.main(verbosity=2)
