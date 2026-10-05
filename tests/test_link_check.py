import json
import os
import unittest

from tests.fixture import VaultCase, run_script, write, BODY


class LinkCheck(VaultCase):
    def result(self, *extra):
        p = run_script("link_check.py", self.vault, "--json", *extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_page_count_skips_tooling_and_cold_folders(self):
        # index, alpha, beta, gamma, bom, orphan, stub
        self.assertEqual(self.result()["pages"], 7)

    def test_broken_links_found_only_in_counted_pages(self):
        broken = self.result()["broken"]
        self.assertEqual(broken, [{"page": os.path.join("wiki", "alpha.md"), "target": "Missing Page"}])

    def test_orphans(self):
        self.assertEqual(self.result()["orphans"], [os.path.join("wiki", "orphan.md")])

    def test_stubs(self):
        self.assertEqual(self.result()["stubs"], [os.path.join("wiki", "stub.md")])

    def test_aliases_and_piped_links_and_anchors_resolve(self):
        r = self.result()
        # [[Gamma|The Gamma]], [[beta#Heading]], [[Bee]] and [[Bom alias]] are not broken
        self.assertEqual(len(r["broken"]), 1)
        self.assertNotIn(os.path.join("wiki", "beta.md"), r["orphans"])
        self.assertNotIn(os.path.join("wiki", "bom.md"), r["orphans"])  # BOM file's alias is read

    def test_path_and_extension_links_resolve(self):
        write(self.vault, "wiki/paths.md", f"# P\n{BODY}\n[[wiki/orphan]] [[orphan.md]]\n")
        r = self.result()
        self.assertEqual(r["broken"][0]["target"], "Missing Page")
        self.assertEqual(len(r["broken"]), 1)
        self.assertNotIn(os.path.join("wiki", "orphan.md"), r["orphans"])

    def test_link_count_ignores_self_links_and_duplicates(self):
        write(self.vault, "wiki/self.md", f"# S\n{BODY}\n[[self]] [[self]] [[orphan]] [[orphan]]\n")
        r = self.result()
        self.assertEqual(r["pages"], 8)
        before = self.result()["links"]
        self.assertEqual(before, r["links"])
        self.assertIn(os.path.join("wiki", "self.md"), r["orphans"])  # only links to itself

    def test_crlf_frontmatter_aliases(self):
        write(self.vault, "wiki/crlf.md", f"---\ntype: concept\naliases: [Crlf alias]\n---\n# C\n{BODY}\n", newline="\r\n")
        write(self.vault, "wiki/user.md", f"# U\n{BODY}\n[[Crlf alias]]\n")
        r = self.result()
        self.assertEqual(len(r["broken"]), 1)
        self.assertNotIn(os.path.join("wiki", "crlf.md"), r["orphans"])

    def test_include_counts_skipped_folders(self):
        r = self.result("--include", "archive,journal")
        self.assertEqual(r["pages"], 9)
        self.assertEqual([b["target"] for b in r["broken"]].count("nowhere-at-all"), 2)

    def test_include_raw_and_templates(self):
        r = self.result("--include", "raw,templates,scripts,output")
        self.assertEqual(r["pages"], 11)

    def test_hidden_dirs_never_included(self):
        self.assertEqual(self.result("--include", ".obsidian")["pages"], 7)

    def test_text_output(self):
        p = run_script("link_check.py", self.vault)
        self.assertEqual(p.returncode, 0)
        self.assertIn("pages: 7", p.stdout)
        self.assertIn("broken links: 1", p.stdout)
        self.assertIn("[[Missing Page]]", p.stdout)

    def test_not_a_directory(self):
        p = run_script("link_check.py", os.path.join(self.tmp, "nope"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("not a directory", p.stderr)

    def test_empty_vault(self):
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        p = run_script("link_check.py", empty, "--json")
        self.assertEqual(json.loads(p.stdout)["pages"], 0)


if __name__ == "__main__":
    unittest.main()
