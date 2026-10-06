"""A small fixture vault and a subprocess runner shared by the script tests."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.environ.get("SCRIPTS_DIR") or os.path.join(ROOT, "scripts")
BODY = " ".join(["word"] * 45)  # long enough that a page is not a stub


def write(vault, rel, text, newline="\n", bom=False):
    """Write text as UTF-8 bytes so line endings and a BOM are exactly as given."""
    path = os.path.join(vault, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = text.replace("\n", newline).encode("utf-8")
    with open(path, "wb") as fh:
        fh.write((b"\xef\xbb\xbf" if bom else b"") + data)
    return path


def build_vault(vault):
    """Pages (all counted unless noted):

    index            links alpha, beta, gamma, a path link and an alias
    wiki/alpha       concept; links beta, [[Gamma|The Gamma]], beta#heading, one broken link
    wiki/beta        entity; alias Bee; links alpha
    wiki/gamma       CRLF file; type person; links Bee (alias) and alpha
    wiki/bom         UTF-8 BOM; alias [Bom alias]; linked from index
    wiki/orphan      nothing links here
    wiki/stub        short, and linked from index
    Skipped by default: raw/, archive/, journal/, templates/, scripts/, output/,
    .obsidian/, README.md and CLAUDE.md files.
    """
    write(vault, "index.md",
          f"# Index\n{BODY}\n[[alpha]] [[beta]] [[gamma]] [[wiki/alpha]] [[Bom alias]] [[stub]]\n")
    write(vault, "wiki/alpha.md",
          f"---\ntype: concept\n---\n# Alpha\n{BODY}\n[[beta]] [[Gamma|The Gamma]] [[beta#Heading]] [[Missing Page]]\n")
    write(vault, "wiki/beta.md",
          f"---\ntype: entity\naliases: [Bee, \"Beta page\"]\n---\n# Beta\n{BODY}\n[[alpha]]\n")
    write(vault, "wiki/gamma.md",
          f"---\r\ntype: person\r\n---\r\n# Gamma\r\n{BODY}\r\n[[Bee]] [[alpha]]\r\n", newline="\n")
    write(vault, "wiki/bom.md",
          f"---\ntype: concept\naliases: [Bom alias]\n---\n# Bom\n{BODY}\n", bom=True)
    write(vault, "wiki/orphan.md", f"---\ntype: concept\n---\n# Orphan\n{BODY}\n")
    write(vault, "wiki/stub.md", "# Stub\nToo short.\n")
    for skipped in ("raw/source.md", "archive/old.md", "journal/day.md", "templates/page.md",
                    "scripts/notes.md", "output/report.md", ".obsidian/cfg.md", "README.md",
                    "CLAUDE.md", "wiki/README.md"):
        write(vault, skipped, f"# Skipped\n{BODY}\n[[alpha]] [[nowhere-at-all]]\n")


def run_script(name, *args):
    """Run a script in a fresh interpreter, as a user would. Returns CompletedProcess."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)


class VaultCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = self._tmp.name
        self.vault = os.path.join(self.tmp, "vault")
        os.makedirs(self.vault)
        build_vault(self.vault)
