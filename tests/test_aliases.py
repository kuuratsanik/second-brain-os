"""Alias parsing: quoted items with commas and colons, block lists, resolution."""
import importlib.util
import json
import os
import unittest

from tests.fixture import SCRIPTS, VaultCase, run_script, write, BODY

NAMES = ("link_check", "vault_stats", "graph_export")


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fm(line):
    return f"---\n{line}\n---\nbody"


class AliasParsing(unittest.TestCase):
    def check(self, text, expected):
        for n in NAMES:
            self.assertEqual(load(n).aliases_of(text), expected, n)

    def test_double_quoted_with_comma_and_colon(self):
        self.check(fm('aliases: ["Õppimise plaan: mida, kuidas", foo]'),
                   ["Õppimise plaan: mida, kuidas", "foo"])

    def test_single_quoted_and_escapes(self):
        self.check(fm("aliases: ['it''s, ok', \"a\\\"b, c\"]"), ["it's, ok", 'a"b, c'])

    def test_plain_flow_and_empty(self):
        self.check(fm("aliases: [Bee, Bom alias]"), ["Bee", "Bom alias"])
        self.check(fm("aliases: []"), [])
        self.check(fm("type: x"), [])

    def test_unclosed_flow_list_stops_at_next_key(self):
        self.check(fm("aliases: [a, b\ntype: concept"), ["a", "b"])

    def test_multiline_flow_list(self):
        self.check(fm("aliases: [a,\n  b]\ntype: x"), ["a", "b"])

    def test_anchor_and_tag_are_stripped(self):
        self.check(fm("aliases: &x [a, b]"), ["a", "b"])
        self.check(fm("aliases: !!seq [a, 'b, c']"), ["a", "b, c"])
        self.check(fm("aliases: &x\n  - &y one\n  - two"), ["one", "two"])

    def test_block_list(self):
        self.check(fm("aliases:\n  - One: two\n  - 'Th, ree'\n  - \"Fo, ur\"\n  - plain # c\ntype: x"),
                   ["One: two", "Th, ree", "Fo, ur", "plain"])


class AliasResolution(VaultCase):
    def setUp(self):
        super().setUp()
        write(self.vault, "wiki/quoted.md",
              f'---\naliases: ["Plan: what, how", \'single, one\']\n---\n# Q\n{BODY}\n')
        write(self.vault, "wiki/block.md", f"---\naliases:\n  - Block alias\n  - 'Block, two'\n---\n# B\n{BODY}\n")
        write(self.vault, "wiki/linker.md",
              f"# L\n{BODY}\n[[Plan: what, how]] [[single, one]] [[Block alias]] [[Block, two]]\n")
        write(self.vault, "index.md",
              f"# Index\n{BODY}\n[[alpha]] [[beta]] [[gamma]] [[Bom alias]] [[stub]] [[quoted]] [[block]] [[linker]]\n")

    def test_links_resolve_through_such_aliases(self):
        p = run_script("link_check.py", self.vault, "--json")
        r = json.loads(p.stdout)
        self.assertEqual([b["target"] for b in r["broken"]], ["Missing Page"])


if __name__ == "__main__":
    unittest.main()
