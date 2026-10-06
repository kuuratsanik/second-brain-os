import datetime
import os
import unittest

from tests.fixture import VaultCase, run_script, write, BODY


class Flags(VaultCase):
    def setUp(self):
        super().setUp()
        self.v = os.path.join(self.tmp, "fresh")
        os.makedirs(self.v)

    def run_flag(self, *args, vault=None):
        p = run_script("link_check.py", vault or self.v, *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        return [l.split("\t") for l in p.stdout.splitlines()]

    def page(self, rel, front="", body=BODY):
        text = f"---\n{front}\n---\n# T\n{body}\n" if front is not None else f"# T\n{body}\n"
        return write(self.v, rel, text)

    def days_ago(self, n):
        return (datetime.date.today() - datetime.timedelta(days=n)).isoformat()

    # --stale
    def test_stale_empty_vault(self):
        self.assertEqual(self.run_flag("--stale", "30"), [])

    def test_stale_no_matches(self):
        self.page("wiki/a.md", f"updated: {self.days_ago(5)}")
        self.page("wiki/b.md", None)  # no frontmatter: mtime is now
        self.assertEqual(self.run_flag("--stale", "30"), [])

    def test_stale_matches_oldest_first_with_fallbacks(self):
        self.page("wiki/mid.md", f"updated: {self.days_ago(100)}")
        self.page("wiki/old.md", f"updated: {self.days_ago(400)}")
        self.page("wiki/created.md", f"created: {self.days_ago(200)}")
        self.page("wiki/both.md", f"created: {self.days_ago(500)}\nupdated: {self.days_ago(1)}")
        self.page("wiki/fresh.md", f"updated: {self.days_ago(10)}")
        rows = self.run_flag("--stale", "90")
        self.assertEqual([r[0] for r in rows], ["wiki/old.md", "wiki/created.md", "wiki/mid.md"])
        self.assertEqual(rows[0][:2], ["wiki/old.md", self.days_ago(400)])
        self.assertIn(rows[0][2], ("400", "401"))  # a run that crosses midnight is one day older

    def test_stale_bad_and_empty_dates_fall_back(self):
        self.page("wiki/bad.md", "updated: not-a-date\ncreated: 2001-02-03")
        self.page("wiki/empty.md", "updated:\ncreated:")      # template left blank: mtime, now
        self.page("wiki/month.md", "updated: 2024-13-45")      # impossible date, no created: mtime
        self.page("wiki/quoted.md", 'updated: "2001-01-01"')
        rows = self.run_flag("--stale", "30")
        self.assertEqual([r[0] for r in rows], ["wiki/quoted.md", "wiki/bad.md"])
        self.assertEqual(rows[1][1], "2001-02-03")

    def test_stale_uses_mtime_without_frontmatter(self):
        path = self.page("wiki/plain.md", None)
        old = (datetime.date.today() - datetime.timedelta(days=60))
        t = datetime.datetime.combine(old, datetime.time(12)).timestamp()
        os.utime(path, (t, t))
        rows = self.run_flag("--stale", "30")
        self.assertEqual(rows[0][:2], ["wiki/plain.md", old.isoformat()])
        self.assertIn(rows[0][2], ("60", "61"))

    def test_stale_odd_date_forms(self):
        self.page("wiki/link.md", "updated: [[2001-01-05]]")
        self.page("wiki/short.md", "updated: 2002-1-5")
        self.page("wiki/time.md", "updated: 2003-01-05T10:00:00Z")
        self.page("wiki/junk.md", "updated: 2004-01-055\ncreated: 2005-01-05")
        rows = {r[0]: r[1] for r in self.run_flag("--stale", "30")}
        self.assertEqual(rows, {"wiki/link.md": "2001-01-05", "wiki/short.md": "2002-01-05",
                                "wiki/time.md": "2003-01-05", "wiki/junk.md": "2005-01-05"})

    def test_stale_warns_on_unparseable_date(self):
        self.page("wiki/bad.md", "updated: sometime\ncreated: 2001-02-03")
        self.page("wiki/blank.md", "updated:")
        p = run_script("link_check.py", self.v, "--stale", "30")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stderr.strip().splitlines(), ["unparseable date: wiki/bad.md"])

    def test_json_output(self):
        import json
        self.page("wiki/old.md", "updated: 2001-01-01\naliases: [Same]")
        self.page("wiki/same.md", None)
        p = run_script("link_check.py", self.v, "--stale", "30", "--duplicates", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        doc = json.loads(p.stdout)
        self.assertEqual(doc["stale"][0]["page"], "wiki/old.md")
        self.assertEqual(doc["duplicates"],
                         [{"kind": "alias", "key": "same", "pages": ["wiki/old.md", "wiki/same.md"]}])

    def test_stale_skips_tooling_folders(self):
        self.page("templates/t.md", "updated: 2001-01-01")
        self.page("raw/r.md", "updated: 2001-01-01")
        self.assertEqual(self.run_flag("--stale", "30"), [])

    def test_stale_rejects_non_integer(self):
        p = run_script("link_check.py", self.v, "--stale", "soon")
        self.assertEqual(p.returncode, 2)

    # --duplicates
    def test_duplicates_empty_vault(self):
        self.assertEqual(self.run_flag("--duplicates"), [])

    def test_duplicates_no_matches(self):
        self.page("wiki/alpha.md", "aliases: [A1]")
        self.page("wiki/beta.md", "aliases: [B1]")
        self.page("wiki/plain.md", None)
        self.assertEqual(self.run_flag("--duplicates"), [])

    def test_duplicates_by_name_ignoring_case_and_punctuation(self):
        self.page("wiki/ml-ops.md", "type: concept")
        self.page("people/ML_Ops.md", "type: concept")
        self.page("wiki/mlops.md", None)
        self.page("wiki/other.md", 'title: "Other: thing"')
        self.page("wiki/other-thing.md", "type: concept")
        rows = self.run_flag("--duplicates")
        self.assertIn(["title", "mlops", "people/ML_Ops.md", "wiki/ml-ops.md", "wiki/mlops.md"], rows)
        self.assertIn(["title", "otherthing", "wiki/other-thing.md", "wiki/other.md"], rows)
        self.assertEqual(len(rows), 2)  # the title field counts, but "other" alone is not "otherthing"

    def test_duplicates_by_title_field(self):
        self.page("wiki/x.md", 'title: "Same Name"')
        self.page("wiki/same-name.md", None)
        self.assertEqual(self.run_flag("--duplicates"),
                         [["title", "samename", "wiki/same-name.md", "wiki/x.md"]])

    def test_alias_equal_to_another_pages_name(self):
        self.page("wiki/postgres.md", "aliases: [PG]")
        self.page("wiki/pg.md", None)
        self.page("wiki/unicode-cafe.md", 'title: "Caf\u00e9"')
        self.page("wiki/cafe-composed.md", 'title: "Cafe\u0301"')
        rows = self.run_flag("--duplicates")
        self.assertIn(["alias", "pg", "wiki/pg.md", "wiki/postgres.md"], rows)
        self.assertIn(["title", "caf\u00e9", "wiki/cafe-composed.md", "wiki/unicode-cafe.md"], rows)

    def test_duplicates_by_shared_alias(self):
        self.page("wiki/one.md", "aliases: [LLM Wiki, one-thing]")
        self.page("wiki/two.md", "aliases:\n  - llm-wiki")
        self.page("wiki/own.md", "aliases: [own]")  # alias equal to its own name is not a duplicate
        rows = self.run_flag("--duplicates")
        self.assertEqual(rows, [["alias", "llmwiki", "wiki/one.md", "wiki/two.md"]])

    def test_flags_do_not_modify_vault(self):
        path = self.page("wiki/a.md", "updated: 2001-01-01")
        def snapshot():
            with open(path, "rb") as fh:
                return fh.read(), os.path.getmtime(path)
        before = snapshot()
        self.run_flag("--stale", "1", "--duplicates")
        self.assertEqual(snapshot(), before)

    def test_missing_vault_still_fails(self):
        p = run_script("link_check.py", os.path.join(self.tmp, "nope"), "--stale", "5")
        self.assertEqual(p.returncode, 1)


if __name__ == "__main__":
    unittest.main()
