import hashlib
import json
from pathlib import Path
import re
import unittest

PROJECT=Path(__file__).resolve().parents[1]
class LockedInterfaces(unittest.TestCase):
    def test_uploaded_baseline_fingerprints(self):
        source=(PROJECT/'setup_sd.sh').read_text()
        expected=json.loads((PROJECT/'tests/locked-sha256.json').read_text())
        for name,digest in expected.items():
            if name.endswith('.png'):
                data=(PROJECT/name).read_bytes()
            elif name=='gui':
                data=re.search(r'''cat <<'EOF' > "\$INSTALL_ROOT/\.sd_gui_app\.py"\n(.*?)\nEOF''',source,re.S).group(1).encode()
            else:
                data=re.search(r'^'+name+r'\(\) \{\n.*?^\}',source,re.M|re.S).group().encode()
            self.assertEqual(hashlib.sha256(data).hexdigest(),digest,name)
