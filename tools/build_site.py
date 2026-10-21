#!/usr/bin/env python3
"""Rebuild the shared navigation on every page.

The site is plain static HTML. This script is the single source of truth for
how the pages are grouped and ordered. It fills in, on every page:

  * the left sidebar (groups and pages, current page highlighted)
  * the breadcrumb under the header
  * the "On this page" rail, built from the page's own <h2 id="..."> headings
  * the Previous / Next pager at the bottom, following the reading order

Run it from the repository root after adding or reordering a page:

    python3 tools/build_site.py

Each page carries marker comments (<!-- site:nav --> ... <!-- /site:nav -->
and so on). Only the text between markers is rewritten; the article body is
never touched. A page without markers is converted once, on first run.
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# The taxonomy. Reading order is top to bottom.
# ---------------------------------------------------------------------------

NAV = [
    {
        "id": "start",
        "title": "Start here",
        "pages": [
            {"path": "/", "title": "Introduction",
             "sub": "What these notes cover, how they are grouped, and the order to read them in."},
        ],
    },
    {
        "id": "core-concepts",
        "title": "Core concepts",
        "desc": "The ideas every retrieval system is built on. Read these first; the later groups assume them.",
        "pages": [
            {"path": "/articles/chunk-size-recall-vs-faithfulness/",
             "title": "Chunk size: recall falls, faithfulness rises",
             "sub": "What happens to a RAG system as chunks grow from 128 to 2,000 tokens: vector dilution hurts search while whole paragraphs help the answer, and why the fix is not a size in the middle.",
             "meta": "19 Oct 2026 · 6 min read"},
            {"path": "/articles/chunk-is-not-the-embedding/",
             "title": "The chunk you embed is not the chunk you retrieve",
             "sub": "Search wants small text and the model wants big text. Decouple the indexed text from the retrieved text: parent-document retrieval, contextual embeddings, and summary or question indexes.",
             "meta": "19 Oct 2026 · 7 min read"},
            {"path": "/articles/chunk-metadata-and-llm-extraction/",
             "title": "Metadata on chunks, and the care needed when a model writes it",
             "sub": "What metadata buys a retrieval system, and the three things that go wrong when a model generates it at ingestion: hallucinated and drifting fields, cost, and injection from the documents. Constrain the schema, validate after, derive security fields from the system.",
             "meta": "21 Oct 2026 · 10 min read"},
        ],
    },
    {
        "id": "chunking-patterns",
        "title": "Chunking patterns",
        "desc": "Applying the core ideas to real corpora, and diagnosing what goes wrong when a chunker changes.",
        "pages": [
            {"path": "/articles/chunking-wiki-pages/",
             "title": "How to chunk wiki pages",
             "sub": "Split on the heading tree, not on token counts. Prepend the page title and heading path, flatten infoboxes to key-value lines, fall back to paragraphs only in long sections, and retrieve the section when a paragraph matches.",
             "meta": "19 Oct 2026 · 8 min read"},
            {"path": "/articles/semantic-chunking-regression/",
             "title": "Semantic chunking made my retrieval evals worse",
             "sub": "Five reasons the switch from fixed 512-token chunks lowers MRR, NDCG and hit rate: variable length, lost overlap, tiny chunks starving the top-k budget, one global distance threshold, and ground truth labelled on the old boundaries. A four-step diagnostic that tells them apart.",
             "meta": "21 Oct 2026 · 10 min read"},
        ],
    },
    {
        "id": "security",
        "title": "Security",
        "desc": "What changes the moment an index holds documents that not every user may read.",
        "pages": [
            {"path": "/articles/cross-tenant-leakage-in-rag/",
             "title": "Cross-tenant leakage in vector search, and how to test for it",
             "sub": "Four ways an ACL-filtered RAG still leaks between tenants: post-filtering after top-k, filters at the prompt layer, a shared semantic cache, and exposed scores. A canary and starvation-probe test plan that finds each one.",
             "meta": "20 Oct 2026 · 9 min read"},
            {"path": "/articles/chunk-permissions-in-sync/",
             "title": "Permissions on chunks, and keeping them in sync",
             "sub": "Put a stable document id on the vector, keep the ACL in a store built for change, pre-filter at query time from the auth token, and let the source system's webhooks or change data capture drive the sync. Filter on groups, not users.",
             "meta": "20 Oct 2026 · 8 min read"},
        ],
    },
    {
        "id": "build-breakdowns",
        "title": "Build breakdowns",
        "desc": "Two systems built end to end, with the measurements and the experiments that did not work.",
        "pages": [
            {"path": "/articles/telugu-gita-rag/",
             "title": "How I built a RAG on the Bhagavad Gita in Telugu",
             "sub": "Preparing the dataset, choosing and fine-tuning the embedding model and reranker, hybrid search, and how it was evaluated.",
             "meta": "15 Sep 2026 · 20 min read"},
            {"path": "/articles/telugu-purana-rag/",
             "title": "Sanskrit in, Telugu out: a RAG over 17 Puranas",
             "sub": "The texts exist only in Sanskrit and the users ask in Telugu. Chapter cards, in-memory retrieval, verse-level citation and on-demand translation, with the measured numbers.",
             "meta": "16 Sep 2026 · 16 min read"},
        ],
    },
]

GITHUB = "https://github.com/viswatejaraavip-ai"

# Bump when style.css or site.js changes, so cached copies are not used with new pages.
ASSET_VERSION = "2"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def flat_pages():
    out = []
    for g in NAV:
        for p in g["pages"]:
            out.append((g, p))
    return out


def file_for(path):
    return ROOT / ("index.html" if path == "/" else path.strip("/") + "/index.html")


def esc(s):
    return html.escape(s, quote=True)


def header_html():
    return (
        '<header class="site">\n'
        '    <button class="menu" type="button" aria-controls="sidenav" aria-expanded="false">Contents</button>\n'
        '    <a class="logo" href="/">ai<span>/</span>engineering<span>/</span>notes</a>\n'
        '    <nav>\n'
        '      <a href="/">Introduction</a>\n'
        f'      <a href="{GITHUB}">GitHub</a>\n'
        '    </nav>\n'
        '  </header>'
    )


def sidebar_html(current):
    parts = []
    for g in NAV:
        parts.append(f'<div class="nav-group">\n      <p class="nav-title">{esc(g["title"])}</p>\n      <ul>')
        for p in g["pages"]:
            cls = ' class="current" aria-current="page"' if p["path"] == current else ""
            parts.append(f'        <li><a href="{p["path"]}"{cls} data-path="{p["path"]}">{esc(p["title"])}</a></li>')
        parts.append("      </ul>\n    </div>")
    return "\n    ".join(parts)


H2 = re.compile(r'<h2 id="([^"]+)">(.*?)</h2>', re.S)
TAG = re.compile(r"<[^>]+>")


def onpage_html(page_html):
    items = []
    for hid, inner in H2.findall(page_html):
        text = TAG.sub("", inner).strip()
        text = re.sub(r"^\d{2}\s*", "", text)  # drop the "01" counter if present
        items.append(f'      <li><a href="#{hid}">{text}</a></li>')
    if not items:
        return ""
    return '<p class="nav-title">On this page</p>\n    <ol>\n' + "\n".join(items) + "\n    </ol>"


def pager_html(idx, pages):
    prev_ = pages[idx - 1][1] if idx > 0 else None
    next_ = pages[idx + 1][1] if idx + 1 < len(pages) else None
    a = []
    if prev_:
        a.append(f'<a class="prev" href="{prev_["path"]}"><small>Previous</small>{esc(prev_["title"])}</a>')
    else:
        a.append("<span></span>")
    if next_:
        a.append(f'<a class="next" href="{next_["path"]}"><small>Next</small>{esc(next_["title"])}</a>')
    return "\n    ".join(a)


def crumbs_html(group, page):
    if page["path"] == "/":
        return ""
    return f'<a href="/#{group["id"]}">{esc(group["title"])}</a> / {esc(page["title"])}'


def groups_html():
    """The group listings for the home page."""
    out = []
    for g in NAV:
        if g["id"] == "start":
            continue
        out.append(f'  <section id="{g["id"]}">\n    <h2 id="h-{g["id"]}">{esc(g["title"])}</h2>\n    <p class="series-desc">{esc(g["desc"])}</p>\n    <ol class="posts">')
        for p in g["pages"]:
            out.append(
                '      <li>\n'
                f'        <a class="post-link" href="{p["path"]}">\n'
                f'          <span class="post-title">{esc(p["title"])}</span>\n'
                '        </a>\n'
                f'        <span class="post-sub">{esc(p["sub"])}</span>\n'
                f'        <span class="post-meta">{esc(p.get("meta", ""))}</span>\n'
                '      </li>'
            )
        out.append("    </ol>\n  </section>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

def fill(page_html, name, content):
    start, end = f"<!-- site:{name} -->", f"<!-- /site:{name} -->"
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pat.search(page_html):
        raise SystemExit(f"marker {name} missing")
    return pat.sub(lambda m: f"{start}\n    {content}\n    {end}" if content else f"{start}{end}", page_html)


def convert(page_html):
    """One-time conversion of an old-layout page to the marker layout."""
    if "<!-- site:nav -->" in page_html:
        return page_html
    s = page_html
    s = re.sub(r'<header class="site">.*?</header>', "<!-- site:header --><!-- /site:header -->", s, count=1, flags=re.S)
    s = re.sub(r'<p class="crumbs">.*?</p>', '<p class="crumbs"><!-- site:crumbs --><!-- /site:crumbs --></p>', s, count=1, flags=re.S)
    s = s.replace(
        "<!-- site:header --><!-- /site:header -->",
        "<!-- site:header --><!-- /site:header -->\n\n"
        '  <div class="layout">\n'
        '  <aside class="sidenav" id="sidenav" aria-label="All notes">\n'
        "    <!-- site:nav --><!-- /site:nav -->\n"
        "  </aside>\n"
        '  <main class="content">',
        1,
    )
    s = s.replace("  <footer>", '  <nav class="pager" aria-label="Reading order">\n    <!-- site:pager --><!-- /site:pager -->\n  </nav>\n\n  <footer>', 1)
    s = s.replace(
        "  </footer>",
        "  </footer>\n"
        "  </main>\n"
        '  <aside class="onpage" aria-label="On this page">\n'
        "    <!-- site:onpage --><!-- /site:onpage -->\n"
        "  </aside>\n"
        "  </div>",
        1,
    )
    s = s.replace("</body>", '<script src="/site.js"></script>\n</body>', 1)
    s = s.replace('href="/#notes"', 'href="/"').replace('href="/#series"', 'href="/"')
    return s


def build():
    pages = flat_pages()
    for idx, (group, page) in enumerate(pages):
        f = file_for(page["path"])
        s = f.read_text()
        s = convert(s)
        s = fill(s, "header", header_html())
        s = fill(s, "nav", sidebar_html(page["path"]))
        if page["path"] != "/":
            s = fill(s, "crumbs", crumbs_html(group, page))
        else:
            s = fill(s, "groups", groups_html())
        s = fill(s, "onpage", onpage_html(s))
        s = fill(s, "pager", pager_html(idx, pages))
        s = re.sub(r'href="/style\.css(\?v=[^"]*)?"', f'href="/style.css?v={ASSET_VERSION}"', s)
        s = re.sub(r'src="/site\.js(\?v=[^"]*)?"', f'src="/site.js?v={ASSET_VERSION}"', s)
        f.write_text(s)
        print("built", f.relative_to(ROOT))


if __name__ == "__main__":
    build()
