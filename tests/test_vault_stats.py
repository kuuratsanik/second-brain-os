import os
import re
import unittest

from tests.fixture import VaultCase, run_script, write, BODY


def parse(out):
    return {m.group(1): m.group(2) for m in re.finditer(r"^(pages|links|avg degree|orphan rate|words)\s+(\S+)", out, re.M)}


class VaultStats(VaultCase):
    def stats(self, *extra):
        p = run_script("vault_stats.py", self.vault, *extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def test_counts(self):
        out = self.stats()
        s = parse(out)
        self.assertEqual(s["pages"], "7")
        # index 6 (alpha twice); alpha 3 (beta twice); beta 1; gamma 2.
        self.assertEqual(s["links"], "12")
        self.assertEqual(s["avg degree"], "1.71")
        # orphans: orphan only (index is exempt from the rule but has no inbound anyway)
        self.assertEqual(s["orphan rate"], "14.3%")

    def test_types_counted_including_untyped(self):
        out = self.stats()
        self.assertRegex(out, r"concept\s+3")
        self.assertRegex(out, r"untyped\s+2")
        self.assertRegex(out, r"entity\s+1")
        self.assertRegex(out, r"person\s+1")

    def test_most_linked_lists_alpha_first(self):
        out = self.stats()
        first = out.split("most linked:")[1].strip().splitlines()[0]
        self.assertTrue(first.strip().endswith(os.path.join("wiki", "alpha.md")), first)
        self.assertTrue(first.split()[0] == "4")  # index x2, beta, gamma

    def test_aliases_count_as_links(self):
        # [[Bee]] and [[Bom alias]] resolve through aliases, so beta and bom are not orphans
        out = self.stats()
        self.assertNotIn("beta.md\n", out.split("most linked:")[0])
        self.assertEqual(parse(out)["orphan rate"], "14.3%")

    def test_include(self):
        s = parse(self.stats("--include", "archive,journal"))
        self.assertEqual(s["pages"], "9")

    def test_crlf_page_is_typed(self):
        self.assertRegex(self.stats(), r"person\s+1")

    def test_empty_vault_exits_with_message(self):
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        p = run_script("vault_stats.py", empty)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("no markdown files", p.stderr)

    def test_bom_file_type_detected(self):
        write(self.vault, "wiki/bomtyped.md", f"---\ntype: source\n---\n{BODY}\n", bom=True)
        self.assertRegex(self.stats(), r"source\s+1")

    def test_path_link_picks_the_named_folder(self):
        write(self.vault, "people/Ann.md", f"# Ann\n{BODY}\n")
        write(self.vault, "wiki/Ann.md", f"# Ann\n{BODY}\n")
        write(self.vault, "wiki/user2.md", f"# U\n{BODY}\n[[people/Ann]] [[people/Ann]]\n")
        out = self.stats()
        self.assertRegex(out, r"\s2\s+" + re.escape(os.path.join("people", "Ann.md")))
        self.assertRegex(out, r"\s0\s+" + re.escape(os.path.join("wiki", "Ann.md")))


if __name__ == "__main__":
    unittest.main()
