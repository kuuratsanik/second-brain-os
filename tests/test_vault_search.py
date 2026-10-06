import hashlib
import json
import os
import socket
import sys
import threading
import unicodedata
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from tests.fixture import SCRIPTS, VaultCase, run_script, write

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
import vault_search  # noqa: E402

PAD = " ".join(["filler"] * 30)


def page(title="", aliases="", h2="", body="", extra=""):
    front = [f"title: {title}"] if title else []
    if aliases:
        front.append(f"aliases: [{aliases}]")
    if extra:
        front.append(extra)
    head = "---\n" + "\n".join(front) + "\n---\n" if front else ""
    return head + f"# Page\n{PAD}\n" + (f"## {h2}\n" if h2 else "") + body + "\n"


def empty_vault(vault):
    for dirpath, _, names in os.walk(vault):
        for n in names:
            os.remove(os.path.join(dirpath, n))


class Search(VaultCase):
    def setUp(self):
        super().setUp()
        empty_vault(self.vault)  # the shared fixture pages would only add noise

    def hits(self, query, **kw):
        return vault_search.search(self.vault, query, **kw)

    def paths(self, query, **kw):
        return [h["path"] for h in self.hits(query, **kw)]

    def test_ranking_title_alias_heading_body(self):
        write(self.vault, "wiki/body.md", page(body="a note about zebra herds"))
        write(self.vault, "wiki/heading.md", page(h2="Zebra"))
        write(self.vault, "wiki/alias.md", page(title="Other", aliases="Zebra"))
        write(self.vault, "wiki/title.md", page(title="Zebra"))
        self.assertEqual(self.paths("zebra"),
                         ["wiki/title.md", "wiki/alias.md", "wiki/heading.md", "wiki/body.md"])

    def test_hit_shape_and_line_numbers(self):
        text = "---\ntype: concept\n---\n# Notes\nfirst line\n\nnothing here\nthe quokka line\nlast\n"
        write(self.vault, "wiki/a.md", text)
        write(self.vault, "wiki/crlf.md", text.replace("quokka", "quokka quokka"), newline="\r\n")
        write(self.vault, "wiki/bom.md", text, bom=True)
        hits = self.hits("quokka")
        self.assertEqual(len(hits), 3)
        for h in hits:
            self.assertEqual(set(h), {"path", "title", "score", "line", "snippet", "sensitivity"})
            self.assertEqual(h["line"], 8, h)
            self.assertIn("quokka", h["snippet"])
            self.assertLessEqual(len(h["snippet"]), 206)
        # the cited line really is that line of the file
        with open(os.path.join(self.vault, "wiki", "a.md"), encoding="utf-8") as fh:
            self.assertIn("quokka", fh.read().split("\n")[8 - 1])

    def test_best_line_prefers_more_query_terms(self):
        write(self.vault, "wiki/a.md", "# A\nalpha alone\nalpha and beta together\n")
        self.assertEqual(self.hits("alpha beta")[0]["line"], 3)

    def test_long_line_snippet_is_about_200_characters_around_the_match(self):
        write(self.vault, "wiki/a.md", "# A\n" + "word " * 100 + "needle " + "word " * 100 + "\n")
        s = self.hits("needle")[0]["snippet"]
        self.assertIn("needle", s)
        self.assertLessEqual(len(s), 206)
        self.assertGreater(len(s), 150)

    def test_limit_and_empty_result(self):
        for i in range(5):
            write(self.vault, f"wiki/p{i}.md", page(body="lemur"))
        self.assertEqual(len(self.hits("lemur", limit=3)), 3)
        self.assertEqual(self.hits("nothingmatches"), [])

    def test_unicode_exact_and_casefold(self):
        write(self.vault, "wiki/et.md", page(body="Õppimine on tähtis. Šokolaad ja žürii."))
        for q in ("õppimine", "ÕPPIMINE", "šokolaad", "žürii", "TÄHTIS"):
            self.assertEqual(self.paths(q), ["wiki/et.md"], q)

    def test_nfd_text_matches_nfc_query(self):
        nfd = unicodedata.normalize("NFD", "Õppimine")
        write(self.vault, "wiki/et.md", page(body=f"{nfd} on tähtis"))
        self.assertEqual(self.paths("õppimine"), ["wiki/et.md"])

    def test_folded_fallback_scores_lower_and_diacritics_rank_first(self):
        write(self.vault, "wiki/with.md", page(body="õppimine"))
        write(self.vault, "wiki/without.md", page(body="oppimine"))
        got = self.hits("oppimine")
        self.assertEqual([h["path"] for h in got], ["wiki/without.md", "wiki/with.md"])
        self.assertLess(got[1]["score"], got[0]["score"])
        # typing the diacritic is exact: a page without it only matches as a fallback
        got = self.hits("õppimine")
        self.assertEqual(got[0]["path"], "wiki/with.md")
        self.assertLess(got[1]["score"], got[0]["score"])

    def test_different_diacritic_is_not_an_exact_match(self):
        write(self.vault, "wiki/a.md", page(body="tuul"))
        write(self.vault, "wiki/b.md", page(body="tüül"))
        got = self.hits("tuul")
        self.assertEqual(got[0]["path"], "wiki/a.md")
        self.assertLess(got[1]["score"], got[0]["score"])

    def test_folded_line_number(self):
        write(self.vault, "wiki/et.md", "# T\nnothing\nsee õppimine siin\n")
        self.assertEqual(self.hits("oppimine")[0]["line"], 3)

    def test_restricted_excluded_private_included(self):
        write(self.vault, "wiki/secret.md", page(body="hedgehog", extra="sensitivity: restricted"))
        write(self.vault, "wiki/priv.md", page(body="hedgehog", extra="sensitivity: Private"))
        write(self.vault, "wiki/open.md", page(body="hedgehog"))
        got = {h["path"]: h["sensitivity"] for h in self.hits("hedgehog")}
        self.assertEqual(got, {"wiki/priv.md": "private", "wiki/open.md": "normal"})
        got = {h["path"] for h in self.hits("hedgehog", include_restricted=True)}
        self.assertEqual(got, {"wiki/secret.md", "wiki/priv.md", "wiki/open.md"})

    def test_skip_dirs_and_archive_flag(self):
        for d in ("raw", "templates", "journal", "archive", ".obsidian", "scripts", "output"):
            write(self.vault, f"{d}/x.md", page(body="platypus"))
        write(self.vault, "wiki/README.md", page(body="platypus"))
        self.assertEqual(self.hits("platypus"), [])
        self.assertEqual(self.paths("platypus", include_archive=True), ["archive/x.md"])
        self.assertEqual(self.hits("platypus"), [])  # the flag did not leak into the module

    def test_deterministic_order_on_ties(self):
        for n in ("c", "a", "b"):
            write(self.vault, f"wiki/{n}.md", page(body="okapi"))
        self.assertEqual(self.paths("okapi"), ["wiki/a.md", "wiki/b.md", "wiki/c.md"])


# ---------------------------------------------------------------- embeddings

CONCEPTS = [("cat", "kitten", "feline"), ("dog", "puppy", "canine"), ("fish", "trout", "salmon")]


def fake_vector(text):
    t = text.lower()
    return [float(sum(t.count(w) for w in group)) + 0.001 for group in CONCEPTS]


class FakeEmbeddings(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append(body)
        if self.path != "/v1/embeddings" or self.server.fail:
            self.send_response(404 if self.path != "/v1/embeddings" else 500)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        inputs = body["input"] if isinstance(body["input"], list) else [body["input"]]
        data = [{"object": "embedding", "index": i, "embedding": fake_vector(t)}
                for i, t in reversed(list(enumerate(inputs)))]  # out of order on purpose
        out = json.dumps({"object": "list", "model": "fake-model", "data": data}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


class Embed(VaultCase):
    def setUp(self):
        super().setUp()
        empty_vault(self.vault)
        write(self.vault, "wiki/cats.md", "# Cats\nThe cat sleeps. A cat purrs.\n")
        write(self.vault, "wiki/dogs.md", "# Dogs\nThe dog barks.\n")
        write(self.vault, "wiki/fish.md", "# Fish\nA trout swims.\n")
        write(self.vault, "wiki/secret.md", "---\nsensitivity: restricted\n---\n# S\nkitten kitten kitten\n")
        self.server = HTTPServer(("127.0.0.1", 0), FakeEmbeddings)
        self.server.requests, self.server.fail = [], False
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.cache = os.path.join(self.tmp, "emb.json")

    def search(self, q, **kw):
        info, warnings = {}, []
        hits = vault_search.search(self.vault, q, embed_url=self.url, embed_cache=self.cache,
                                   info=info, warn=warnings.append, **kw)
        return hits, info, warnings

    def texts_sent(self):
        return [t for r in self.server.requests for t in r["input"]]

    def test_hybrid_finds_a_page_with_no_shared_word(self):
        self.assertEqual(vault_search.search(self.vault, "kitten"), [])  # BM25 alone: nothing
        hits, info, warnings = self.search("kitten")
        self.assertEqual(warnings, [])
        self.assertEqual(info["mode"], "hybrid")
        self.assertEqual(hits[0]["path"], "wiki/cats.md")
        self.assertGreater(hits[0]["line"], 0)
        self.assertNotIn("wiki/secret.md", [h["path"] for h in hits])

    def test_restricted_text_is_never_sent(self):
        self.search("kitten")
        self.assertFalse([t for t in self.texts_sent() if "kitten kitten" in t])
        self.search("kitten", include_restricted=True)
        self.assertTrue([t for t in self.texts_sent() if "kitten kitten" in t])

    def test_lexical_and_semantic_agree_ranks_first(self):
        hits, _, _ = self.search("cat")
        self.assertEqual(hits[0]["path"], "wiki/cats.md")

    def test_cache_hit_and_miss(self):
        info = self.search("cat")[1]
        self.assertEqual((info["hits"], info["misses"]), (0, 3))
        with open(self.cache, encoding="utf-8") as fh:
            doc = json.load(fh)
        self.assertEqual(doc["model"], "fake-model")
        self.assertEqual(len(doc["vectors"]), 3)
        chunk = "Cats\n# Cats\nThe cat sleeps. A cat purrs."
        self.assertIn(hashlib.sha256(chunk.encode("utf-8")).hexdigest(), doc["vectors"])

        self.server.requests[:] = []
        info = self.search("dog")[1]
        self.assertEqual((info["hits"], info["misses"]), (3, 0))
        self.assertEqual(self.texts_sent(), ["dog"])  # only the query

        write(self.vault, "wiki/dogs.md", "# Dogs\nThe dog barks at a puppy.\n")
        self.server.requests[:] = []
        info = self.search("dog")[1]
        self.assertEqual((info["hits"], info["misses"]), (2, 1))
        self.assertEqual(len(self.texts_sent()), 2)  # the query and the one changed chunk
        self.assertIn("puppy", self.texts_sent()[1])
        with open(self.cache, encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh)["vectors"]), 3)  # the stale chunk is dropped

    def test_default_cache_location(self):
        vault_search.search(self.vault, "cat", embed_url=self.url, warn=lambda m: None)
        self.assertTrue(os.path.isfile(os.path.join(self.vault, ".cache", "embeddings.json")))

    def test_server_error_falls_back(self):
        self.server.fail = True
        hits, info, warnings = self.search("cat")
        self.assertEqual(info["mode"], "bm25")
        self.assertEqual(len(warnings), 1)
        self.assertEqual(hits[0]["path"], "wiki/cats.md")

    def test_cli_server_down_warns_and_exits_zero(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        p = run_script("vault_search.py", self.vault, "cat", "--json",
                       "--embed-url", f"http://127.0.0.1:{port}")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("warning", p.stderr)
        doc = json.loads(p.stdout)
        self.assertEqual(doc["mode"], "bm25")
        self.assertEqual(doc["hits"][0]["path"], "wiki/cats.md")

    def test_cli_hybrid(self):
        p = run_script("vault_search.py", self.vault, "kitten", "--json",
                       "--embed-url", self.url, "--embed-cache", self.cache)
        self.assertEqual(p.returncode, 0, p.stderr)
        doc = json.loads(p.stdout)
        self.assertEqual(doc["mode"], "hybrid")
        self.assertEqual(doc["hits"][0]["path"], "wiki/cats.md")

    def test_changed_model_rebuilds_cache(self):
        self.search("cat")
        with open(self.cache, encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["model"] = "older-model"
        with open(self.cache, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        self.server.requests[:] = []
        self.search("cat")
        self.assertEqual(len(self.texts_sent()), 4)  # the query and all three chunks again
        with open(self.cache, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["model"], "fake-model")

    def test_corrupt_cache_is_ignored(self):
        with open(self.cache, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        hits, info, warnings = self.search("cat")
        self.assertEqual((info["mode"], warnings), ("hybrid", []))


class Cli(VaultCase):
    def test_exit_codes(self):
        self.assertEqual(run_script("vault_search.py", self.vault, "alpha").returncode, 0)
        self.assertEqual(run_script("vault_search.py", self.vault, "nosuchword").returncode, 0)
        p = run_script("vault_search.py", os.path.join(self.tmp, "missing"), "x")
        self.assertEqual(p.returncode, 1)
        self.assertIn("not a directory", p.stderr)
        self.assertEqual(run_script("vault_search.py", self.vault).returncode, 2)
        self.assertEqual(run_script("vault_search.py", self.vault, "x", "--limit", "0").returncode, 2)
        self.assertEqual(run_script("vault_search.py", self.vault, "x", "--bogus").returncode, 2)
        self.assertEqual(run_script("vault_search.py", self.vault, "  ").returncode, 2)

    def test_text_output_cites_path_and_line(self):
        p = run_script("vault_search.py", self.vault, "alpha", "--limit", "1")
        self.assertRegex(p.stdout, r"^1\. wiki/alpha\.md:\d+  ")

    def test_no_hits_text(self):
        self.assertEqual(run_script("vault_search.py", self.vault, "nosuchword").stdout.strip(), "no hits")

    def test_json_shape_and_unicode_not_escaped(self):
        write(self.vault, "wiki/et.md", "# Õppimine\nõppimine on tähtis\n")
        out = run_script("vault_search.py", self.vault, "õppimine", "--json").stdout
        doc = json.loads(out)
        self.assertEqual(set(doc), {"query", "mode", "count", "hits"})
        self.assertEqual(doc["mode"], "bm25")
        self.assertEqual(doc["hits"][0]["title"], "Õppimine")
        self.assertIn("õppimine", out)

    def test_vault_is_not_modified(self):
        before = sorted(os.walk(self.vault))
        run_script("vault_search.py", self.vault, "alpha")
        self.assertEqual(before, sorted(os.walk(self.vault)))


if __name__ == "__main__":
    unittest.main()
