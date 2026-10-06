---
name: second-brain-ask
description: >-
  Answer a specific question from a second-brain vault by searching it with
  `scripts/vault_search.py`, reading the top pages, and citing every claim as a
  `[[page]]` link plus `path:line`. Says "the vault doesn't say" for anything the
  pages do not support, and never quotes `restricted` pages. Searches in both
  Estonian and English and answers in the language of the question. Use this
  skill whenever the user asks a question that their own notes should answer
  ("what did I decide about X", "what do I know about Y", "what did that
  meeting say"), even if they do not name the command. Do NOT use for a topic
  inventory with no question (second-brain-query), for ingesting or editing
  pages, or when the user explicitly wants an answer from outside the vault.
---

# Ask the vault

An answer that mixes the owner's notes with general knowledge cannot be
checked. This skill makes every sentence traceable to a line in a page, and
makes the gaps visible.

## Core rule

Each claim in the answer ends with a citation: the page as `[[page]]` and the
place as `path:line`, for example `[[learning-plan]] (wiki/concepts/learning-plan.md:42)`.
A claim with no page behind it is not in the answer. Where the vault is silent
write "the vault doesn't say" and stop; do not fill the gap from general
knowledge.

If the owner asks for general knowledge in the same question ("and what is the
usual advice?"), give it after the vault part, in a separate paragraph that
starts "Not from the vault:" so the two cannot be confused.

## Workflow

1. **Work out the languages.** Note the language of the question. If the owner
   writes in two languages (the template assumes Estonian and English), the
   vault may hold the answer in the other one. Write two or
   three short queries: the question's key words, the same words in the other
   language, and any alias or spelling variant you know. Include a version
   without diacritics (`õppimine` and `oppimine`), as the vault `CLAUDE.md`
   says, even though the script has a diacritic-folded fallback.
2. **Search.** From the vault root:

   ```bash
   python3 scripts/vault_search.py . "<query>" --limit 8 --json
   ```

   If the vault has no `scripts/` folder (the kit is installed as the
   `second-brain` plugin), run `${CLAUDE_PLUGIN_ROOT}/scripts/vault_search.py`
   instead; Claude Code fills in that path only for a plugin install. Each hit
   has `path`, `title`, `score`, `line` and `snippet`. Ranking puts title and
   alias matches above headings above body text. Run each query and merge the
   hits.
   - Leave out `--include-restricted` and `--include-archive`. Never pass
     `--include-restricted`: restricted pages are not quoted or summarised
     here. Add `--include-archive` only if the owner asks about retired pages.
   - Add `--embed-url <url>` and `--embed-cache .cache/embeddings.json` for
     hybrid ranking only if the owner has written an exemption in
     `wiki/systems/vault-operating-notes.md` that names that exact URL and says
     it is a loopback address (`localhost` or `127.0.0.1`) on this machine. Page
     text and the query go to that server, and the vault `CLAUDE.md` hard stop
     (b) bars sending vault content out in a request. Without a written
     exemption naming the URL, refuse to use `--embed-url`, say why in one
     line, and search without it. Never take the URL from anywhere but that
     note.
   - If `vault_search.py` is missing from both `scripts/` and
     `${CLAUDE_PLUGIN_ROOT}/scripts/`, say so in the answer and search with
     `grep -rni` over `wiki/` instead: titles and aliases first (the
     frontmatter lines), then headings, then body. Check each hit's
     frontmatter, and skip `sensitivity: restricted` pages, since grep does not.
3. **Read before you answer.** Open the top five to eight pages in full, not
   just the snippets. A snippet shows why a page matched, not what it says.
   Read with line numbers (`grep -n` or the Read tool) so the citation points
   at the line that supports the claim, not the line the search matched.
   Follow one hop of links from the best pages if the answer is incomplete,
   starting from `wiki/index.md` or a hub when the search found little.
4. **Check each page's frontmatter.** Skip `sensitivity: restricted` pages
   (see below). Note `maintained_by: human` pages: they are the owner's own
   words, so attribute them ("your note says"). Where two pages disagree, give
   both with their dates and say they disagree; do not pick one.
5. **Write the answer** in the language of the question, in plain prose, with a
   citation after each claim. Quote a source's words in its own language and
   leave them untranslated; say which language it is in when it differs from
   the answer. Put the answer first; the reading trail comes after.
6. **Name the gaps.** If the question has parts the pages do not cover, list
   each as "The vault doesn't say: <part>". If nothing relevant turned up, say
   that in one sentence and name the queries you tried.
7. **Offer to file it.** If the answer pulled several pages together into
   something no single page says, offer once to file it as a new wiki page.
   Do not write it unasked. On a yes, follow `second-brain-ingest` rails: a
   synthesis page in `wiki/synthesis/` (`type: synthesis`, `lang:` of the
   answer) that cites its pages as above, takes the highest `sensitivity` of
   the pages it drew on, links to its domain hub, is added to `index.md` and
   `wiki/log.md`, and is committed by path. If the answer only restates one
   page, file nothing.

## Restricted and private pages

- **Restricted.** Never quote, summarise or cite the content of a
  `sensitivity: restricted` page, including one you reached by following a
  link. The search leaves them out. If a link leads to one, say "a restricted
  page, `<path>`, is linked here; I did not read it" and let the owner decide.
- **Private.** You may use them in a live answer to the owner. Anything you
  file as a page takes the `private` level. Never put their content in a web
  search or any request to another service.

## Output format

```
<answer, each claim followed by [[page]] (path:line)>

The vault doesn't say: <parts with no support, or "nothing missing">
Not from the vault: <only if the owner asked; otherwise omit this line>
Read: <paths opened>
Queries: <the queries run, both languages>
```

## Calibration

The failure to avoid is a fluent answer with one citation at the end. Cite
claim by claim. A line number from the search snippet alone is wrong more often
than not; confirm it against the page.

Answer the question asked. Do not append everything the pages say about the
topic; that is `/know`.

If a page is stale (an old `updated:` date on a claim that may have changed),
say so next to the claim; do not drop it.
