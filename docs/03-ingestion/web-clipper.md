# Web articles

Articles are the bulk of what most people save, and the browser is where the
decision to save happens. Anything that requires switching windows loses.

## Obsidian Web Clipper

The [official extension](https://obsidian.md/clipper) from the Obsidian team.
Per Obsidian's [Web Clipper
help](https://help.obsidian.md/web-clipper), it is available for Chrome, Brave,
Arc, Orion and other Chromium-based browsers, for Firefox, for Safari and for
Edge. It uses [Defuddle](https://github.com/kepano/defuddle) to capture only the
main content of a page and saves it as markdown straight into your vault.

Install it, open the settings, and set the destination folder to `raw/clippings/`, which is where the
[vault template](../../vault-template/raw/README.md) expects web articles.

## Template

The default template saves the page body. Add frontmatter so the agent knows
what it is holding without re-reading the whole file:

```
---
title: {{title}}
source: {{url}}
author: {{author}}
published: {{published}}
clipped: {{date}}
type: article
---

{{content}}
```

These are Web Clipper's
[preset variables](https://help.obsidian.md/web-clipper/variables).
`{{author}}` and `{{published}}` come back empty on plenty of sites. That is
fine, an empty field is better than a guessed one, and the agent handles the
gap by saying the source is undated rather than inventing a date.

## What to clip

Clip what you would want to find again in a year: primary sources, engineering
posts, papers, documentation, arguments you disagree with and want to answer
later.

Skip news that will be stale in a week, listicles, and anything you are saving
out of guilt. Every low-value page you ingest costs twice: once at ingest, and
again every time the agent reads past it looking for something else.

The honest test at clip time is whether you can name what you would ask this
source later. If you cannot, do not clip it.

## Awkward pages

- **Paywalls.** The clipper saves what the browser rendered. If you can read it,
  it can save it. If you cannot, it saves the paywall notice, so check before
  moving on.
- **Documentation sites.** Clipping page by page is a losing game. Save the
  entry point and let the agent fetch the rest, or clone the docs repo into
  `raw/` if it is open source.
- **Single-page apps and dynamic content.** The main-content extraction sometimes
  returns a fragment (Obsidian's
  [troubleshooting page](https://help.obsidian.md/web-clipper/troubleshoot) says
  it can be overly conservative and describes how to bypass it). Look at the file before ingest.
- **Threads and comment sections.** The value is usually in the replies, which
  the clipper drops. Copy the thread manually or screenshot it into
  `raw/assets/`.

## Clip now, ingest later

Clipping and ingesting are separate steps on purpose. Clip freely during the
day, run `/ingest` in one batch later, because ingesting one source at a time
gives the agent no chance to spot that three things you saved this week are
about the same idea.

## Next

[YouTube and podcasts](youtube-transcripts.md)
