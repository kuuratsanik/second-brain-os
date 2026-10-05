import json
import os
import unittest

from tests.fixture import VaultCase, run_script

LONG = " ".join(["word"] * 30)


class ChatExport(VaultCase):
    def convert(self, data, *extra, bom=False):
        src = os.path.join(self.tmp, "conversations.json")
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        with open(src, "wb") as fh:
            fh.write((b"\xef\xbb\xbf" if bom else b"") + raw)
        out = os.path.join(self.tmp, "raw")
        p = run_script("chat_export_to_md.py", src, out, "--min-words", "20", *extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        return out, p.stdout

    def read(self, out, name):
        with open(os.path.join(out, name), encoding="utf-8") as fh:
            return fh.read()

    def claude_conv(self, name="Plan: the week", **kw):
        conv = {"name": name, "created_at": "2025-03-04T10:00:00Z",
                "chat_messages": [{"sender": "human", "text": LONG},
                                  {"sender": "assistant", "text": "Reply " + LONG}]}
        conv.update(kw)
        return conv

    def test_claude_shape(self):
        out, stdout = self.convert([self.claude_conv()])
        self.assertEqual(os.listdir(out), ["plan-the-week.md"])
        text = self.read(out, "plan-the-week.md")
        self.assertIn('title: "Plan: the week"', text)  # colon would break unquoted YAML
        self.assertIn("created: 2025-03-04", text)
        self.assertIn("**human**", text)
        self.assertIn("**assistant**", text)
        self.assertIn("wrote 1 files", stdout)

    def test_short_conversations_skipped(self):
        short = self.claude_conv("Tiny", chat_messages=[{"sender": "human", "text": "hi"}])
        out, stdout = self.convert([short, self.claude_conv()])
        self.assertEqual(os.listdir(out), ["plan-the-week.md"])
        self.assertIn("skipped 1 short", stdout)

    def test_duplicate_titles_do_not_overwrite(self):
        out, _ = self.convert([self.claude_conv(), self.claude_conv()])
        self.assertEqual(sorted(os.listdir(out)), ["plan-the-week-2.md", "plan-the-week.md"])

    def test_chatgpt_mapping_shape(self):
        conv = {"title": "GPT chat", "create_time": 1741082400.0, "mapping": {
            "a": {"message": {"author": {"role": "user"}, "create_time": 2, "content": {"parts": [LONG]}}},
            "b": {"message": {"author": {"role": "assistant"}, "create_time": 3, "content": {"parts": ["Answer " + LONG, {"x": 1}]}}},
            "root": {"message": None},
            "s": {"message": {"author": {"role": "system"}, "create_time": 1, "content": {"parts": ["hidden"]}}},
        }}
        out, _ = self.convert([conv])
        text = self.read(out, "gpt-chat.md")
        self.assertIn("created: 2025-03-04", text)
        self.assertLess(text.index("**user**"), text.index("**assistant**"))
        self.assertNotIn("hidden", text)

    def test_wrapped_in_conversations_key_and_bom(self):
        out, _ = self.convert({"conversations": [self.claude_conv()]}, bom=True)
        self.assertEqual(os.listdir(out), ["plan-the-week.md"])

    def test_list_content_blocks(self):
        conv = self.claude_conv(chat_messages=[{"sender": "human", "content": [{"type": "text", "text": LONG}, "extra"]}])
        out, _ = self.convert([conv])
        self.assertIn("extra", self.read(out, "plan-the-week.md"))

    def test_unrecognised_shapes_do_not_crash(self):
        out, stdout = self.convert([42, "x", {"name": "No messages"}])
        self.assertIn("wrote 0 files", stdout)

    def test_non_ascii_title_and_slug(self):
        out, _ = self.convert([self.claude_conv("Õppimise plaan / 学习")])
        self.assertEqual(os.listdir(out), ["õppimise-plaan-学习.md"])

    def test_untitled_and_unsafe_title(self):
        out, _ = self.convert([self.claude_conv("../../etc/passwd")])
        self.assertEqual(os.listdir(out), ["etcpasswd.md"])
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "etc")))

    def test_bad_shape_exits(self):
        src = os.path.join(self.tmp, "bad.json")
        with open(src, "w") as fh:
            fh.write('"just a string"')
        p = run_script("chat_export_to_md.py", src, os.path.join(self.tmp, "o"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("unrecognised export shape", p.stderr)

    def test_crlf_json_file(self):
        src = os.path.join(self.tmp, "crlf.json")
        raw = json.dumps([self.claude_conv()], indent=2).replace("\n", "\r\n")
        with open(src, "wb") as fh:
            fh.write(raw.encode("utf-8"))
        out = os.path.join(self.tmp, "o")
        p = run_script("chat_export_to_md.py", src, out, "--min-words", "20")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(os.listdir(out), ["plan-the-week.md"])

    def test_mapping_walks_children_with_null_timestamps(self):
        def node(role, text, parent, children):
            return {"parent": parent, "children": children,
                    "message": {"author": {"role": role}, "create_time": None, "content": {"parts": [text]}}}
        conv = {"title": "Tree", "mapping": {
            "c": node("assistant", "THIRD " + LONG, "b", []),
            "a": node("user", "FIRST " + LONG, "root", ["b"]),
            "b": node("assistant", "SECOND " + LONG, "a", ["c"]),
            "root": {"parent": None, "children": ["a"], "message": None},
        }}
        out, _ = self.convert([conv])
        text = self.read(out, "tree.md")
        self.assertLess(text.index("FIRST"), text.index("SECOND"))
        self.assertLess(text.index("SECOND"), text.index("THIRD"))

    def test_mapping_follows_current_node_branch(self):
        def node(text, parent, children):
            return {"parent": parent, "children": children,
                    "message": {"author": {"role": "user"}, "content": {"parts": [text]}}}
        conv = {"title": "Branch", "current_node": "new", "mapping": {
            "root": {"parent": None, "children": ["old", "new"], "message": None},
            "old": node("OLDBRANCH " + LONG, "root", []),
            "new": node("NEWBRANCH " + LONG, "root", []),
        }}
        out, _ = self.convert([conv])
        text = self.read(out, "branch.md")
        self.assertIn("NEWBRANCH", text)
        self.assertNotIn("OLDBRANCH", text)


if __name__ == "__main__":
    unittest.main()
