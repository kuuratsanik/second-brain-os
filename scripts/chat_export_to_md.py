#!/usr/bin/env python3
"""Convert an exported chat history JSON into one markdown file per conversation.

Usage:
    python3 chat_export_to_md.py conversations.json ./raw --min-words 150

Works with the common export shape used by Claude and ChatGPT: a JSON array of
conversations, each with a name/title and a list of messages. Unknown shapes are
skipped with a warning rather than guessed at.

Read the privacy page before running this on a real export. Chat history is the
single most sensitive thing most people would put in a vault.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone


def slug(text, limit=60):
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    s = re.sub(r"[\s_]+", "-", s)
    return (s[:limit] or "untitled").strip("-")


def text_of(message):
    content = message.get("content", message.get("text", ""))
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, str):
                parts.append(c)
            elif isinstance(c, dict):
                parts.append(c.get("text", ""))
        return "\n".join(p for p in parts if p)
    if isinstance(content, dict):
        return "\n".join(p for p in (content.get("parts") or []) if isinstance(p, str))
    return ""


def date_of(value):
    """YYYY-MM-DD from an ISO string or a Unix timestamp, else an empty string."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%d")
        except (OverflowError, OSError, ValueError):
            return ""
    return str(value or "")[:10]


def mapping_messages(mapping, current=None):
    """ChatGPT's conversations.json keeps messages in a `mapping` of nodes, each
    with `parent` and `children`. Walk the tree rather than trusting timestamps,
    which can be null. With `current_node` we follow the branch the user last saw;
    otherwise every branch is walked from the root, depth first."""
    order = []
    if current in mapping:
        node = current
        while isinstance(node, str) and node in mapping and node not in order:
            order.append(node)
            n = mapping[node]
            node = n.get("parent") if isinstance(n, dict) else None
        order.reverse()
    else:
        seen = set()
        stack = [k for k, n in reversed(list(mapping.items()))
                 if isinstance(n, dict) and not (isinstance(n.get("parent"), str)
                                                 and n.get("parent") in mapping)]
        while stack:
            k = stack.pop()
            if not isinstance(k, str) or k in seen or k not in mapping:
                continue
            seen.add(k)
            order.append(k)
            n = mapping[k]
            kids = (n.get("children") if isinstance(n, dict) else None) or []
            stack.extend(reversed(kids if isinstance(kids, list) else []))
        order += [k for k in mapping if k not in seen]  # detached nodes, file order
    out = []
    for k in order:
        node = mapping.get(k)
        m = node.get("message") if isinstance(node, dict) else None
        if not isinstance(m, dict):
            continue
        author = m.get("author")
        role = author.get("role") if isinstance(author, dict) else None
        if role == "system":
            continue
        out.append({"role": role or "unknown", "content": m.get("content", "")})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export")
    ap.add_argument("outdir")
    ap.add_argument("--min-words", type=int, default=150,
                    help="skip conversations shorter than this")
    args = ap.parse_args()

    with open(args.export, encoding="utf-8-sig") as fh:
        data = json.load(fh)

    if isinstance(data, dict):
        data = data.get("conversations", [])
    if not isinstance(data, list):
        sys.exit("unrecognised export shape: expected a list of conversations")

    os.makedirs(args.outdir, exist_ok=True)
    written = skipped = 0

    for conv in data:
        if not isinstance(conv, dict):
            continue
        title = conv.get("name") or conv.get("title") or "untitled"
        created = date_of(conv.get("created_at") or conv.get("create_time"))
        messages = conv.get("chat_messages") or conv.get("messages") or []
        if not messages and isinstance(conv.get("mapping"), dict):
            messages = mapping_messages(conv["mapping"], conv.get("current_node"))
        if isinstance(messages, dict):
            messages = list(messages.values())

        body = []
        for m in messages:
            if not isinstance(m, dict):
                continue
            role = m.get("sender") or m.get("role") or "unknown"
            t = text_of(m).strip()
            if t:
                body.append(f"**{role}**\n\n{t}\n")

        joined = "\n".join(body)
        if len(joined.split()) < args.min_words:
            skipped += 1
            continue

        quoted = json.dumps(str(title), ensure_ascii=False)  # a colon in a title must not break the YAML
        front = (f"---\ntitle: {quoted}\nsource: chat export\n"
                 f"created: {created}\n---\n\n# {title}\n\n")
        path = os.path.join(args.outdir, f"{slug(str(title))}.md")
        n = 2
        while os.path.exists(path):
            path = os.path.join(args.outdir, f"{slug(str(title))}-{n}.md")
            n += 1
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(front + joined)
        written += 1

    print(f"wrote {written} files to {args.outdir}, skipped {skipped} short conversations")


if __name__ == "__main__":
    main()
