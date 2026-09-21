import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/'piapps/reboot.py'
class Reboot(unittest.TestCase):
    def fixture(self,root,status='installed',token='same',fresh=True):
        state=root/'state';state.mkdir()
        manager=root/'pi-apps';(manager/'data/status').mkdir(parents=True)
        receipt=state/'receipt.json';receipt.write_text(json.dumps({'token':token}))
        marker=manager/'data/status/Stable Diffusion';marker.write_text(status)
        if not fresh: os.utime(marker,ns=(1,1))
        return [str(SCRIPT),'2147483647','0',str(manager),str(state),'same']
    def test_reboot_only_after_matching_commit_and_new_status(self):
        with tempfile.TemporaryDirectory() as directory:
            argv=self.fixture(Path(directory))
            with patch('sys.argv',argv),patch('subprocess.run') as call:
                runpy.run_path(str(SCRIPT),run_name='__main__')
                call.assert_called_once_with(['sudo','-n','reboot'],check=True)
    def test_no_reboot_on_failure_old_status_or_wrong_token(self):
        for status,token,fresh in [('corrupted','same',True),('installed','other',True),('installed','same',False)]:
            with tempfile.TemporaryDirectory() as directory:
                argv=self.fixture(Path(directory),status,token,fresh)
                with patch('sys.argv',argv),patch('subprocess.run') as call:
                    with self.assertRaises(SystemExit):runpy.run_path(str(SCRIPT),run_name='__main__')
                    call.assert_not_called()
    def test_timeout_does_not_reboot(self):
        with tempfile.TemporaryDirectory() as directory:
            argv=self.fixture(Path(directory))
            argv[1]=str(os.getpid())
            argv[2]=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]
            with patch('sys.argv',argv),patch('subprocess.run') as call,patch('time.sleep'):
                with self.assertRaises(SystemExit):runpy.run_path(str(SCRIPT),run_name='__main__')
                call.assert_not_called()
