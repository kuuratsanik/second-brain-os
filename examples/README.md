# Examples

Worked examples of what the system produces. Everything here is fictional.

## Demo vault

[`demo-vault/`](demo-vault/) is a small vault in the shape the Quickstart
creates, filled with invented material: an imaginary analyst, invented
articles by invented authors, invented colleagues and a made-up company.
Nothing in it is real, and none of its claims should be cited. Every page
carries a line saying so.

It shows the page contract from
[`vault-template/CLAUDE.md`](../vault-template/CLAUDE.md) in use. It does not
copy the template's `CLAUDE.md`, `templates/`, skills or settings, because those
change; copy them from `vault-template/` when you build your own. It also omits
the `hub-personal` and `hub-creative` hubs and the four `wiki/systems/` pages the
template ships (routing, lifecycle, operating notes and needs-owner), so its
`index.md` lists four hubs where yours will list six.

What to look at:

- **A full chain:** the journal entry `journal/2026-09-06.md`, the idea
  `fifteen-minute-friday-review`, the experiment `friday-review-trial`, its
  review and the adopted system `friday-review`. The success measure is written
  before the start date, and the review compares the result against the
  expectation, including one the owner got wrong.
- **A dropped idea kept as evidence:** `morning-flashcards`.
- **Mixed languages:** `wiki/sources/2026-09-14-oppimise-plaan.md` is an
  Estonian source. The file name is ASCII (`oppimise-plaan`), the `title:` keeps
  `Õppimise plaan: loe vähem, mäleta rohkem`, and the original form is in
  `aliases:`. The page body is in Estonian. The concept it feeds,
  `retrieval-practice`, is in English because its sources split one to one and
  English wins a tie; the Estonian term `Meenutuspraktika` is an alias.
- **Disagreement recorded, not resolved:** `synthesis/review-cadence.md` sets
  two sources that disagree on spacing (ten days against seven) side by side.
- **A merge and an archive:** `log.md` records `spaced-repetition` merged into
  `retrieval-practice` and archived with `archived_reason` and
  `merged_into` under `archive/`. Nothing was deleted. The commit id in the log
  line is invented.
- **A meeting** built from `templates/meeting.md`, and two **person pages**
  marked `private`.
- **Hubs, `index.md` and `log.md`** kept current, including a Gaps section.

### Layout

```
archive/wiki/concepts/spaced-repetition.md
journal/2026-09-06.md
journal/2026-09-14.md
journal/2026-09-21.md
journal/2026-09-28.md
raw/clippings/2026-08-12-fifteen-minute-weekly-review.md
raw/clippings/2026-09-03-retrieval-practice-at-work.md
raw/clippings/2026-09-14-oppimise-plaan.md
raw/meetings/2026-09-22-q4-planning-sync.md
raw/youtube/2026-09-29-notes-that-link-back.md
wiki/concepts/note-linking.md
wiki/concepts/retrieval-practice.md
wiki/concepts/time-boxing.md
wiki/concepts/weekly-review.md
wiki/entities/anu-kask.md
wiki/entities/kuusk-analytics.md
wiki/entities/margin.md
wiki/entities/mihkel-sepp.md
wiki/hubs/hub-learning.md
wiki/hubs/hub-self-improvement.md
wiki/hubs/hub-systems.md
wiki/hubs/hub-work.md
wiki/index.md
wiki/log.md
wiki/self-improvement/experiments/friday-review-trial.md
wiki/self-improvement/ideas/fifteen-minute-friday-review.md
wiki/self-improvement/ideas/morning-flashcards.md
wiki/self-improvement/reviews/friday-review-trial-review.md
wiki/sources/2026-08-12-fifteen-minute-weekly-review.md
wiki/sources/2026-09-03-retrieval-practice-at-work.md
wiki/sources/2026-09-14-oppimise-plaan.md
wiki/sources/2026-09-22-q4-planning-sync.md
wiki/sources/2026-09-29-notes-that-link-back.md
wiki/synthesis/review-cadence.md
wiki/systems/friday-review.md
```

### What healthy numbers look like

Run on the vault as committed:

```
$ python3 scripts/link_check.py examples/demo-vault
pages: 25
links: 143 (avg 5.72 per page)
broken links: 0
orphans: 0
stubs (<40 words): 0

$ python3 scripts/vault_stats.py examples/demo-vault
pages          25
  source       5
  hub          4
  concept      4
  entity       4
  idea         2
  log          1
  index        1
  review       1
  experiment   1
  system       1
  synthesis    1
words          4,676
links          169
avg degree     6.76
orphan rate    0.0%

most linked:
    13  wiki/concepts/weekly-review.md
    13  wiki/synthesis/review-cadence.md
    11  wiki/concepts/retrieval-practice.md
    10  wiki/sources/2026-09-22-q4-planning-sync.md
     8  wiki/concepts/time-boxing.md
     8  wiki/sources/2026-08-12-fifteen-minute-weekly-review.md
     8  wiki/self-improvement/reviews/friday-review-trial-review.md
     8  wiki/systems/friday-review.md
     7  wiki/hubs/hub-learning.md
     7  wiki/hubs/hub-self-improvement.md
```

Reading them:

- **Broken links, orphans and stubs are all zero.** Every page has at least one
  inbound link, which in practice means it is listed on a hub and in
  `index.md`. A rising orphan rate is the usual sign that ingestion is running
  without linking.
- **Link counts differ between the two scripts.** `link_check.py` counts each
  distinct pair of pages once (143). `vault_stats.py` counts every link
  occurrence (169). Compare a script's numbers with its own earlier runs, not
  with the other script's.
- **Average degree around six or seven** is what a vault with hubs and an index
  looks like when every page links back to its hub. Both scripts skip `raw/`,
  `journal/`, `output/`, `archive/` and `templates/`, so those folders do not
  affect the counts.
- **This is a small vault.** At 25 pages it is easy to keep clean. The numbers
  worth watching are the trend, not the level.

## Planned

- A vault at 30 days and at 6 months, from a real vault, with what broke
- A research report generated from a vault, with the pages it drew on

Contributions of real, anonymised examples are welcome. Read
[CONTRIBUTING.md](../CONTRIBUTING.md) first.
