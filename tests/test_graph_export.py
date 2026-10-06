import csv
import os
import unittest
import xml.etree.ElementTree as ET

from tests.fixture import VaultCase, run_script, write, BODY

NS = "{http://graphml.graphdrawing.org/xmlns}"


class GraphExport(VaultCase):
    def export(self, fmt, *extra):
        out = os.path.join(self.tmp, "out." + ("csv" if fmt == "csv" else "graphml"))
        p = run_script("graph_export.py", self.vault, out, "--format", fmt, *extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        return out, p.stdout

    def test_missing_vault_fails(self):
        out = os.path.join(self.tmp, "out.csv")
        p = run_script("graph_export.py", os.path.join(self.tmp, "nope"), out)
        self.assertEqual(p.returncode, 1)
        self.assertIn("not a directory", p.stderr)
        self.assertFalse(os.path.exists(out))

    def test_vault_is_a_file_fails(self):
        f = write(self.tmp, "afile.md", "x")
        p = run_script("graph_export.py", f, os.path.join(self.tmp, "o.csv"))
        self.assertEqual(p.returncode, 1)
        self.assertIn("not a directory", p.stderr)

    def test_unwritable_output(self):
        p = run_script("graph_export.py", self.vault, os.path.join(self.tmp, "no", "dir", "o.csv"))
        self.assertEqual(p.returncode, 1)
        self.assertIn("cannot write", p.stderr)
        self.assertNotIn("Traceback", p.stderr)

    def test_csv_shape(self):
        out, stdout = self.export("csv")
        with open(out, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        self.assertEqual(rows[0], ["source", "target"])
        edges = [tuple(r) for r in rows[1:]]
        self.assertEqual(len(edges), 12)  # repeated links are kept: index and alpha each repeat one
        self.assertIn(("alpha", "beta"), edges)
        self.assertIn(("alpha", "gamma"), edges)       # [[Gamma|The Gamma]]
        self.assertIn(("gamma", "beta"), edges)        # [[Bee]] alias
        self.assertIn(("index", "bom"), edges)         # alias in a BOM file
        self.assertNotIn(("alpha", "Missing Page"), edges)
        self.assertEqual(edges.count(("index", "alpha")), 2)
        self.assertIn("7 nodes, 12 edges", stdout)

    def test_csv_has_no_edges_from_skipped_folders(self):
        out, _ = self.export("csv")
        with open(out, encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotIn("nowhere", text)
        self.assertNotIn("old,", text)

    def test_graphml_shape(self):
        out, stdout = self.export("graphml")
        root = ET.parse(out).getroot()
        self.assertEqual(root.tag, NS + "graphml")
        key = root.find(NS + "key")
        self.assertEqual((key.get("id"), key.get("for"), key.get("attr.name")), ("t", "node", "type"))
        graph = root.find(NS + "graph")
        self.assertEqual(graph.get("edgedefault"), "directed")
        nodes = {n.get("id"): n.find(NS + "data").text for n in graph.findall(NS + "node")}
        self.assertEqual(set(nodes), {"index", "alpha", "beta", "gamma", "bom", "orphan", "stub"})
        self.assertEqual(nodes["alpha"], "concept")
        self.assertEqual(nodes["beta"], "entity")
        self.assertEqual(nodes["gamma"], "person")
        self.assertEqual(nodes["index"], "untyped")
        edges = graph.findall(NS + "edge")
        self.assertEqual(len(edges), 12)
        self.assertEqual([e.get("id") for e in edges], [f"e{i}" for i in range(12)])
        ids = set(nodes)
        for e in edges:
            self.assertIn(e.get("source"), ids)
            self.assertIn(e.get("target"), ids)
        self.assertIn("7 nodes, 12 edges", stdout)

    def test_graphml_escapes_special_characters(self):
        write(self.vault, "wiki/a&b.md", f"---\ntype: x<y\n---\n{BODY}\n[[alpha]]\n")
        out, _ = self.export("graphml")
        root = ET.parse(out).getroot()  # parse fails if unescaped
        ids = {n.get("id") for n in root.iter(NS + "node")}
        self.assertIn("a&b", ids)

    def test_include(self):
        out, stdout = self.export("csv", "--include", "archive")
        self.assertIn("8 nodes, 13 edges", stdout)  # old -> alpha

    def test_crlf_page_edges(self):
        out, _ = self.export("csv")
        with open(out, newline="", encoding="utf-8") as fh:
            edges = [tuple(r) for r in csv.reader(fh)]
        self.assertIn(("gamma", "alpha"), edges)

    def test_default_format_is_csv(self):
        out = os.path.join(self.tmp, "default.csv")
        p = run_script("graph_export.py", self.vault, out)
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(fh.readline().strip(), "source,target")

    def test_same_name_pages_are_distinct_nodes(self):
        write(self.vault, "people/Ann.md", f"# Ann\n{BODY}\n")
        write(self.vault, "wiki/Ann.md", f"# Ann\n{BODY}\n")
        write(self.vault, "wiki/user2.md", f"# U\n{BODY}\n[[people/Ann]] [[wiki/Ann]]\n")
        out, _ = self.export("csv")
        with open(out, newline="", encoding="utf-8") as fh:
            edges = [tuple(r) for r in csv.reader(fh)]
        self.assertIn(("user2", "people/Ann"), edges)
        self.assertIn(("user2", "wiki/Ann"), edges)
        out, stdout = self.export("graphml")
        ids = {n.get("id") for n in ET.parse(out).getroot().iter(NS + "node")}
        self.assertTrue({"people/Ann", "wiki/Ann", "alpha"} <= ids)
        self.assertNotIn("Ann", ids)


if __name__ == "__main__":
    unittest.main()
