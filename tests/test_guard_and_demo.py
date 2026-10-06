"""Runs the vault guard's own test file, and checks the demo vault stays healthy."""
import json
import os
import subprocess
import sys
import unittest

from tests.fixture import ROOT, run_script

GUARD_TESTS = os.path.join(ROOT, "vault-template", ".claude", "hooks", "test_guard.py")
DEMO = os.path.join(ROOT, "examples", "demo-vault")


class GuardSuite(unittest.TestCase):
    def test_guard_test_file_passes(self):
        p = subprocess.run([sys.executable, GUARD_TESTS], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=900)
        # every line that is not an "ok" line (the FAIL lines and the closing list), not the tail
        # of the output, so a failure on one platform shows its case names in the CI log
        not_ok = "\n".join(ln for ln in p.stdout.splitlines() if not ln.startswith("ok  "))
        self.assertEqual(p.returncode, 0, not_ok[-20000:] + p.stderr[-4000:])
        self.assertRegex(p.stdout, r"(\d+)/\1 passed")


class DemoVault(unittest.TestCase):
    def test_no_broken_links_or_orphans(self):
        p = run_script("link_check.py", DEMO, "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertGreater(r["pages"], 0)
        self.assertEqual(r["broken"], [])
        self.assertEqual(r["orphans"], [])


if __name__ == "__main__":
    unittest.main()
