import json
import os
import re
import unittest

from tests.fixture import BODY, VaultCase, run_script, write

TODAY = "2026-10-06"


class Dashboard(VaultCase):
    def data(self, *extra):
        p = run_script("dashboard.py", self.vault, "--json", "--today", TODAY, *extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def html(self, *extra):
        out = os.path.join(self.tmp, "out", "d.html")
        p = run_script("dashboard.py", self.vault, "--out", out, "--today", TODAY, *extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(out, "rb") as fh:
            return fh.read().decode("utf-8")

    def test_counts_match_link_check(self):
        lcheck = json.loads(run_script("link_check.py", self.vault, "--json").stdout)
        c = self.data()["counts"]
        self.assertEqual(c["pages"], lcheck["pages"])
        self.assertEqual(c["links"], lcheck["links"])
        self.assertEqual(c["broken"], len(lcheck["broken"]))
        self.assertEqual(c["orphans"], len(lcheck["orphans"]))
        self.assertEqual(c["stubs"], len(lcheck["stubs"]))

    def test_deterministic(self):
        write(self.vault, "wiki/dup.md", f"---\ntitle: Alpha\n---\n# Dup\n{BODY}\n")
        a, b = self.html(), self.html()
        self.assertEqual(a, b)
        p1 = run_script("dashboard.py", self.vault, "--json", "--today", TODAY).stdout
        p2 = run_script("dashboard.py", self.vault, "--json", "--today", TODAY).stdout
        self.assertEqual(p1, p2)

    def test_default_out_is_in_the_vault_and_file_is_bytes_identical(self):
        p = run_script("dashboard.py", self.vault, "--today", TODAY)
        self.assertEqual(p.returncode, 0, p.stderr)
        path = os.path.join(self.vault, "output", "dashboard.html")
        with open(path, "rb") as fh:
            first = fh.read()
        self.assertNotIn(b"\r", first)
        run_script("dashboard.py", self.vault, "--today", TODAY)
        with open(path, "rb") as fh:
            self.assertEqual(first, fh.read())  # output/ is skipped, so it never counts as a page

    def test_self_contained_and_accessible(self):
        h = self.html()
        self.assertTrue(h.startswith("<!doctype html>"))
        self.assertIn('<html lang="en">', h)
        self.assertIn("prefers-color-scheme:dark", h)
        self.assertIn("<svg", h)
        self.assertIn("<h1>", h)
        self.assertIn('class="skip"', h)
        self.assertNotRegex(h, r"<script|<link|@import|https?://|src=|url\(")
        # every bar has its number as text, and the SVG is hidden from screen readers
        self.assertIn('aria-hidden="true"', h)
        self.assertEqual(len(re.findall(r"<h2 id=", h)), len(re.findall(r"<section aria-labelledby=", h)))

    def test_restricted_pages_show_only_their_path(self):
        write(self.vault, "wiki/secret.md",
              f"---\ntitle: SECRETTITLE\naliases: [SECRETALIAS]\nsensitivity: restricted\n---\n"
              f"# SECRETHEADING\nSECRETBODY {BODY}\n[[SECRETTARGET]]\n")
        write(self.vault, "wiki/twin.md", f"---\ntitle: SECRETALIAS\n---\n# Twin\n{BODY}\n")
        h, d = self.html(), run_script("dashboard.py", self.vault, "--json", "--today", TODAY).stdout
        for text in (h, d):
            for word in ("SECRETTITLE", "SECRETALIAS", "SECRETHEADING", "SECRETBODY", "SECRETTARGET"):
                self.assertNotIn(word, text, word)
        self.assertIn("wiki/secret.md", h)  # listed by path (it is an orphan with a broken link)
        data = json.loads(d)
        self.assertEqual(data["counts"]["restricted"], 1)
        self.assertEqual([b["target"] for b in data["broken"] if b["page"] == "wiki/secret.md"], [None])
        self.assertTrue(any(g["name"] == "(restricted)" for g in data["duplicates"]))

    def test_html_is_escaped(self):
        write(self.vault, "wiki/x.md", f"# X\n{BODY}\n[[<img src=x onerror=alert(1)>]]\n")
        h = self.html()
        self.assertNotIn("<img", h)
        self.assertIn("&lt;img", h)

    def test_stale_and_stale_days(self):
        write(self.vault, "wiki/old.md", f"---\nupdated: 2025-01-01\n---\n# Old\n{BODY}\n")
        write(self.vault, "wiki/new.md", f"---\nupdated: 2026-10-01\n---\n# New\n{BODY}\n")
        stale = {s["page"]: s["age_days"] for s in self.data()["stale"]}
        self.assertEqual(stale["wiki/old.md"], 643)
        self.assertNotIn("wiki/new.md", stale)
        self.assertIn("wiki/new.md", {s["page"] for s in self.data("--stale-days", "2")["stale"]})

    def test_duplicates(self):
        write(self.vault, "wiki/people/ann.md", f"# Ann\n{BODY}\n")
        write(self.vault, "wiki/orgs/Ann.md", f"# Ann\n{BODY}\n")
        groups = [g for g in self.data()["duplicates"] if g["name"] == "ann"]
        self.assertEqual(groups[0]["pages"], ["wiki/orgs/Ann.md", "wiki/people/ann.md"])

    def test_lifecycle_funnel(self):
        for name, kind, status in [("i1", "idea", "new"), ("i2", "idea", "considering"),
                                   ("i3", "idea", "promoted"), ("i4", "idea", "dropped"),
                                   ("e1", "experiment", "planned"), ("e2", "experiment", "active"),
                                   ("e3", "experiment", "reviewing"), ("e4", "experiment", "adopted"),
                                   ("e5", "experiment", "dropped"), ("e6", "experiment", "odd"),
                                   ("s1", "system", "active"), ("s2", "system", "draft")]:
            write(self.vault, f"wiki/{name}.md", f"---\ntype: {kind}\nstatus: {status}\n---\n# T\n{BODY}\n")
        lc = self.data()["lifecycle"]
        self.assertEqual(lc["stages"], {"idea": 2, "plan": 1, "experiment": 2, "adopted": 1, "dropped": 2})
        self.assertEqual(lc["promoted"], 1)
        self.assertEqual(lc["other"], {"odd": 1})  # system pages with status active never count

    def test_restricted_status_is_not_named_in_the_funnel(self):
        front = "---\ntype: {}\nstatus: {}\nsensitivity: restricted\n---\n# R\n" + BODY + "\n"
        write(self.vault, "wiki/r1.md", front.format("experiment", "SECRETSTATUS"))
        write(self.vault, "wiki/r2.md", front.format("idea", "promoted"))
        write(self.vault, "wiki/o1.md", f"---\ntype: experiment\nstatus: oddity\n---\n# O\n{BODY}\n")
        d = self.data()["lifecycle"]
        self.assertEqual(d["other"], {"(restricted)": 2, "oddity": 1})
        self.assertEqual(d["promoted"], 0)
        self.assertNotIn("SECRETSTATUS", self.html())
        self.assertNotIn("SECRETSTATUS", run_script("dashboard.py", self.vault, "--json").stdout)

    def test_folders_and_most_linked(self):
        d = self.data()
        folders = {f["folder"]: f["pages"] for f in d["folders"]}
        self.assertEqual(folders, {"(root)": 1, "wiki": 6})
        self.assertEqual(d["most_linked"][0], {"page": "wiki/alpha.md", "inbound": 3})
        self.assertLessEqual(len(d["most_linked"]), 10)

    def test_most_linked_capped_at_ten(self):
        for i in range(12):
            write(self.vault, f"wiki/h{i}.md", f"# H{i}\n{BODY}\n[[h{(i + 1) % 12}]] [[index]]\n")
        self.assertEqual(len(self.data()["most_linked"]), 10)

    def test_needs_owner_queue(self):
        self.assertIsNone(self.data()["needs_owner_open"])
        write(self.vault, "wiki/systems/needs-owner.md", """---
title: Needs owner
---
# Needs owner

- a bullet in the intro that is not an entry under Done is counted
## Waiting

- **2026-10-04, one.** First entry
  continues here
  - a nested bullet is part of the entry
- **2026-10-05, two.** Second
- [ ] a checkbox item
- [x] a ticked item
```
- inside a fence
```

## Done

- **2026-09-11, finished.** Done entry
- another
""")
        self.assertEqual(self.data()["needs_owner_open"], 4)
        write(self.vault, "wiki/systems/needs-owner.md", "# N\n\n## Waiting\n\n_Nothing yet._\n\n## Done\n\n_Nothing yet._\n")
        self.assertEqual(self.data()["needs_owner_open"], 0)

    def test_exit_codes(self):
        self.assertEqual(run_script("dashboard.py", os.path.join(self.tmp, "missing")).returncode, 1)
        self.assertEqual(run_script("dashboard.py").returncode, 2)
        self.assertEqual(run_script("dashboard.py", self.vault, "--stale-days", "x").returncode, 2)
        self.assertEqual(run_script("dashboard.py", self.vault, "--stale-days", "-1").returncode, 2)
        self.assertEqual(run_script("dashboard.py", self.vault, "--today", "soon").returncode, 2)
        self.assertEqual(run_script("dashboard.py", self.vault, "--out",
                                    os.path.join(self.tmp, "ok.html")).returncode, 0)

    def test_empty_vault(self):
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        p = run_script("dashboard.py", empty, "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["counts"]["pages"], 0)
        self.assertEqual(run_script("dashboard.py", empty, "--out", os.path.join(self.tmp, "e.html")).returncode, 0)


if __name__ == "__main__":
    unittest.main()
