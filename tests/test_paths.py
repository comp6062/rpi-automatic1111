import ctypes
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import time
import unittest

SOURCE = (Path(__file__).resolve().parents[1]/'setup_sd.sh').read_text()

class Paths(unittest.TestCase):
    def test_generated_shell_assignments(self):
        body=SOURCE.split('cat > "$RUN_SD_PATH" <<RUNEOF\n',1)[1].split('\nRUNEOF',1)[0]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'spaces "quote" \'single\' $HOME $(touch BAD) `touch BAD2` %f \\ path'
            root.mkdir()
            env=dict(WEBUI_DIR=str(root/'stable-diffusion-webui'), VENV_DIR=str(root/'stable-diffusion-env'), INSTALL_ROOT=str(root), RUN_SD_PATH=str(root/'run_sd.sh'), USER_HOME=str(root), PIAPPS_MODE='0')
            prefix='\n'.join(k+'='+shlex.quote(v) for k,v in env.items())
            result=subprocess.run(['bash','-c',prefix+'\ncat <<RUNEOF\n'+body+'\nRUNEOF'],text=True,capture_output=True,check=True)
            runner=root/'run_sd.sh'; runner.write_text(result.stdout)
            subprocess.run(['bash','-n',str(runner)],check=True)
            assignments=result.stdout.split('\nget_lan_ip()',1)[0]
            result=subprocess.run(['bash','-c',assignments+'\nprintf "%s\\0" "$INSTALL_ROOT" "$WEBUI_DIR" "$USER_HOME" "$PIAPPS_MANAGER"'],capture_output=True,check=True)
            self.assertEqual(result.stdout.split(b'\0')[:-1], [str(root).encode(),str(root/'stable-diffusion-webui').encode(),str(root).encode(),b''])
            self.assertFalse(Path('BAD').exists()); self.assertFalse(Path('BAD2').exists())
    def test_desktop_exec_real_glib_parser(self):
        gio=ctypes.CDLL('libgio-2.0.so.0')
        gio.g_desktop_app_info_new_from_filename.argtypes=[ctypes.c_char_p]
        gio.g_desktop_app_info_new_from_filename.restype=ctypes.c_void_p
        gio.g_app_info_launch.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
        gio.g_app_info_launch.restype=ctypes.c_int
        quote=re.search(r'^desktop_exec_quote\(\) \{\n.*?^\}',SOURCE,re.M|re.S).group()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'spaces "quote" \'single\' $HOME `echo` %f \\ text'
            root.mkdir()
            executable=root/'runner.sh'
            marker=Path(directory)/'launched'
            executable.write_text('#!/bin/bash\nprintf done > '+shlex.quote(str(marker))+'\n')
            executable.chmod(0o755)
            quoted=subprocess.check_output(['bash','-c',quote+'\ndesktop_exec_quote "$1"','test',str(executable)],text=True)
            desktop=Path(directory)/'test.desktop'
            desktop.write_text('[Desktop Entry]\nType=Application\nName=Test\nExec=/bin/bash '+quoted+'\nTerminal=false\n')
            info=gio.g_desktop_app_info_new_from_filename(str(desktop).encode())
            self.assertTrue(info,'GLib rejected desktop entry')
            self.assertTrue(gio.g_app_info_launch(info,None,None,None),'GLib failed to launch path')
            for _ in range(40):
                if marker.exists(): break
                time.sleep(.05)
            self.assertEqual(marker.read_text(),'done')

if __name__=='__main__': unittest.main(verbosity=2)
