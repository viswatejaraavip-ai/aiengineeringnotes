#!/usr/bin/env python3
"""Rebuild the shared navigation on every page.

The site is plain static HTML. This script is the single source of truth for
how the pages are grouped and ordered. It fills in, on every page:

  * the left sidebar: a tree of sections > topics > notes, current page marked
  * the breadcrumb under the header
  * the "On this page" rail, built from the page's own <h2 id="..."> headings
  * the Previous / Next pager at the bottom, following the reading order
  * on the home page, the listing of every section and topic

Run it from the repository root after adding or moving a page:

    python3 tools/build_site.py

Each page carries marker comments (<!-- site:nav --> ... <!-- /site:nav -->
and so on). Only the text between markers is rewritten; the article body is
never touched. A page without markers is converted once, on first run.
"""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GITHUB = "https://github.com/viswatejaraavip-ai"

# Bump when style.css or site.js changes, so cached copies are not used with new pages.
ASSET_VERSION = "3"

# ---------------------------------------------------------------------------
# The taxonomy: sections > topics > (optional sub-groups of) notes.
# Reading order is top to bottom. A topic with no notes is listed as empty.
# ---------------------------------------------------------------------------

def T(id_, title, groups=None, desc=""):
    return {"id": id_, "title": title, "groups": groups or [], "desc": desc}


RAG_INGESTION_GROUPS = [
    {
        "title": "Core concepts",
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
        "title": "Chunking patterns",
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
        "title": "Multi-tenant indexes",
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
        "title": "Build breakdowns",
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

LLM_FUNDAMENTALS_GROUPS = [
    {
        "title": "Tokenization",
        "pages": [
            {"path": "/articles/byte-pair-encoding/",
             "title": "Byte-pair encoding, and why tokenizers work on bytes",
             "sub": "Merge the most frequent adjacent pair until the vocabulary is full, with the classic four-word example worked by hand. Then why the base alphabet is the 256 UTF-8 bytes: no unknown token, a tiny base vocabulary, one pipeline for every script and for code, at the cost of more tokens for scripts the corpus is thin on.",
             "meta": "24 Oct 2026 · 9 min read"},
        ],
    },
    {
        "title": "Transformer internals",
        "pages": [
            {"path": "/articles/attention-qkv-and-scaling/",
             "title": "Why attention has separate Q, K and V, and why it divides by √d_k",
             "sub": "Three projections let a token ask one thing, advertise another and hand over a third, which one similarity matrix cannot express. The dot product of two d_k-dimensional vectors has variance d_k, so without scaling the softmax saturates and its gradient vanishes.",
             "meta": "24 Oct 2026 · 8 min read"},
            {"path": "/articles/mixture-of-experts-active-vs-total/",
             "title": "Mixture of experts: active parameters versus total parameters",
             "sub": "Several feed-forward experts and a router that sends each token to one or two of them. Why memory is paid on the total count and arithmetic on the active count, with Mixtral and DeepSeek-V3 as examples, where the bandwidth advantage fades under batching, and what learned routing costs in training.",
             "meta": "24 Oct 2026 · 9 min read"},
        ],
    },
]

INFERENCE_SCALING_GROUPS = [
    {
        "title": "Serving fundamentals",
        "pages": [
            {"path": "/articles/kv-cache-memory-bound-decoding/",
             "title": "The KV cache, and why decoding is memory-bound",
             "sub": "Caching keys and values makes generation linear instead of quadratic, and leaves each decode step streaming the whole model and cache for one token's worth of arithmetic. The size formula, worked for a 70B model at 2k and 128k with and without grouped-query attention, and the mitigations: MQA, GQA, paged attention, cache quantisation.",
             "meta": "24 Oct 2026 · 10 min read"},
            {"path": "/articles/grouped-query-attention/",
             "title": "Grouped-query attention: the middle ground between MHA and MQA",
             "sub": "One key-value pair per query head, per group, or for all heads. Why sharing one pair per group shrinks the cache by the group ratio, keeps quality close to multi-head, and became the default in Llama, Mistral and Gemma, with the real head counts. How a trained multi-head model converts by mean-pooling and uptraining.",
             "meta": "24 Oct 2026 · 7 min read"},
        ],
    },
    {
        "title": "Decoding",
        "pages": [
            {"path": "/articles/temperature-top-k-top-p-and-t0/",
             "title": "Temperature, top-k, top-p, and why T = 0 is not deterministic",
             "sub": "The sampling pipeline in the order it runs: temperature divides, top-k cuts by rank, top-p cuts by mass, then softmax and a draw. Temperature zero is argmax, and still varies run to run: floating-point sums depend on order, kernels change strategy with batch size, near-ties at the top flip, and the continuation diverges.",
             "meta": "24 Oct 2026 · 9 min read"},
        ],
    },
]

AGENT_ARCHITECTURES_GROUPS = [
    {
        "title": "Agent loops",
        "pages": [
            {"path": "/articles/function-calling-model-and-application/",
             "title": "Function calling: how the model decides, and what your code must do",
             "sub": "Tool definitions are prompt text; the decision to call is learned judgement; strict mode guarantees the arguments' shape but not their sense. Then the application's four steps, parse, validate and authorise, execute, return, with a worked order-lookup example and the mistakes that matter, starting with treating the model's arguments as permission.",
             "meta": "25 Oct 2026 · 9 min read"},
            {"path": "/articles/react-pattern-and-function-calling/",
             "title": "The ReAct pattern as a loop of function calls",
             "sub": "Thought, action and observation mapped onto a modern API: the reasoning before a call, the structured tool-call block and its stop reason, the tool-result message your code appends, and the exit when the model answers without a tool. A full loop in pseudocode, why structured calls beat parsing text, and what the loop needs that the paper did not cover.",
             "meta": "25 Oct 2026 · 10 min read"},
        ],
    },
]

NAV = [
    {"id": "foundations", "title": "Foundations", "topics": [
        T("llm-fundamentals", "LLM fundamentals", LLM_FUNDAMENTALS_GROUPS,
          desc="How the models themselves work: how text becomes tokens, the pieces of the Transformer, and the reasons behind the choices in them."),
        T("frontier-models", "Frontier models and the model landscape"),
        T("prompting", "Prompting and context engineering"),
        T("fine-tuning", "Fine-tuning, alignment and post-training"),
    ]},
    {"id": "inference", "title": "Inference and reasoning", "topics": [
        T("inference-scaling", "Inference scaling and serving", INFERENCE_SCALING_GROUPS,
          desc="What it costs to run a model: where the time goes in a decode step, what memory is spent on, and the levers a serving stack has."),
        T("test-time-compute", "Test-time compute and reasoning models"),
    ]},
    {"id": "agents", "title": "Agentic AI", "topics": [
        T("agent-architectures", "Agent architectures, tool use and MCP", AGENT_ARCHITECTURES_GROUPS,
          desc="How a model is turned into something that acts: the loop, the tools, the protocol between them, and the controls around it."),
        T("multi-agent", "Multi-agent systems, orchestration and human-in-the-loop"),
    ]},
    {"id": "rag", "title": "RAG", "topics": [
        T("rag-ingestion", "RAG ingestion, chunking and indexing", RAG_INGESTION_GROUPS,
          desc="Everything that happens before a query arrives: how text is split, what is embedded, what metadata rides along, and how an index stays correct when it holds documents not everyone may read."),
        T("rag-retrieval", "RAG retrieval: embeddings, hybrid search and reranking"),
        T("rag-generation", "RAG generation, grounding and debugging"),
        T("rag-advanced", "Advanced RAG: agentic RAG, GraphRAG, memory and long context"),
    ]},
    {"id": "evaluation", "title": "Evaluation, observability and ops", "topics": [
        T("eval-fundamentals", "Evaluation fundamentals, benchmarks and LLM-as-judge"),
        T("eval-systems", "Evaluating RAG, agents and production systems"),
        T("observability", "Observability, tracing and monitoring"),
        T("llmops", "LLMOps, cost, reliability and product engineering"),
    ]},
    {"id": "security", "title": "Security, red teaming and governance", "topics": [
        T("prompt-injection", "Prompt injection and LLM application security"),
        T("red-teaming", "Red teaming, adversarial testing and guardrails"),
        T("governance", "AI governance, risk and compliance"),
        T("responsible-ai", "Responsible AI, safety, alignment and societal risk"),
    ]},
]

HOME = {"path": "/", "title": "Introduction"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def flat_pages():
    """Reading order: (section, topic, group, page). The home page comes first."""
    out = [(None, None, None, HOME)]
    for sec in NAV:
        for topic in sec["topics"]:
            for group in topic["groups"]:
                for page in group["pages"]:
                    out.append((sec, topic, group, page))
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


def topic_has(topic, path):
    return any(p["path"] == path for g in topic["groups"] for p in g["pages"])


def sidebar_html(current):
    """A tree: section > topic > (group label) > notes. Open along the current path.

    On the home page the one topic that has notes is opened, so the tree is not
    a wall of closed sections for a first-time visitor.
    """
    home_attrs = ' class="nav-home current" aria-current="page"' if current == "/" else ' class="nav-home"'
    out = [f'<a{home_attrs} href="/" data-path="/">Introduction</a>']
    for sec in NAV:
        sec_open = any(topic_has(t, current) for t in sec["topics"]) or (
            current == "/" and any(t["groups"] for t in sec["topics"]))
        out.append(f'<details class="nav-section" data-id="{sec["id"]}"{" open" if sec_open else ""}>')
        out.append(f'      <summary>{esc(sec["title"])}</summary>')
        out.append("      <ul>")
        for t in sec["topics"]:
            if not t["groups"]:
                out.append(f'        <li class="nav-topic empty"><span>{esc(t["title"])}</span></li>')
                continue
            t_open = topic_has(t, current) or current == "/"
            out.append(f'        <li class="nav-topic"><details data-id="{t["id"]}"{" open" if t_open else ""}>')
            out.append(f'          <summary>{esc(t["title"])}</summary>')
            for g in t["groups"]:
                out.append(f'          <p class="nav-sub">{esc(g["title"])}</p>\n          <ul>')
                for p in g["pages"]:
                    cls = ' class="current" aria-current="page"' if p["path"] == current else ""
                    out.append(f'            <li><a href="{p["path"]}"{cls} data-path="{p["path"]}">{esc(p["title"])}</a></li>')
                out.append("          </ul>")
            out.append("        </details></li>")
        out.append("      </ul>\n    </details>")
    return "\n    ".join(out)


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
    prev_ = pages[idx - 1][3] if idx > 0 else None
    next_ = pages[idx + 1][3] if idx + 1 < len(pages) else None
    a = []
    if prev_:
        a.append(f'<a class="prev" href="{prev_["path"]}"><small>Previous</small>{esc(prev_["title"])}</a>')
    else:
        a.append("<span></span>")
    if next_:
        a.append(f'<a class="next" href="{next_["path"]}"><small>Next</small>{esc(next_["title"])}</a>')
    return "\n    ".join(a)


def crumbs_html(sec, topic, page):
    return (f'<a href="/#{sec["id"]}">{esc(sec["title"])}</a> / '
            f'<a href="/#{topic["id"]}">{esc(topic["title"])}</a> / {esc(page["title"])}')


def groups_html():
    """The section and topic listing for the home page."""
    out = []
    for sec in NAV:
        out.append(f'  <section id="{sec["id"]}">\n    <h2 id="h-{sec["id"]}">{esc(sec["title"])}</h2>')
        for t in sec["topics"]:
            out.append(f'    <div class="topic" id="{t["id"]}">\n      <h3>{esc(t["title"])}</h3>')
            if not t["groups"]:
                out.append('      <p class="topic-empty">No notes yet.</p>\n    </div>')
                continue
            if t["desc"]:
                out.append(f'      <p class="series-desc">{esc(t["desc"])}</p>')
            for g in t["groups"]:
                out.append(f'      <p class="eyebrow">{esc(g["title"])}</p>\n      <ol class="posts">')
                for p in g["pages"]:
                    out.append(
                        '        <li>\n'
                        f'          <a class="post-link" href="{p["path"]}">\n'
                        f'            <span class="post-title">{esc(p["title"])}</span>\n'
                        '          </a>\n'
                        f'          <span class="post-sub">{esc(p["sub"])}</span>\n'
                        f'          <span class="post-meta">{esc(p.get("meta", ""))}</span>\n'
                        '        </li>'
                    )
                out.append("      </ol>")
            out.append("    </div>")
        out.append("  </section>")
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
    for idx, (sec, topic, group, page) in enumerate(pages):
        f = file_for(page["path"])
        s = f.read_text()
        s = convert(s)
        s = fill(s, "header", header_html())
        s = fill(s, "nav", sidebar_html(page["path"]))
        if page["path"] == "/":
            s = fill(s, "groups", groups_html())
        else:
            s = fill(s, "crumbs", crumbs_html(sec, topic, page))
        s = fill(s, "onpage", onpage_html(s))
        s = fill(s, "pager", pager_html(idx, pages))
        s = re.sub(r'href="/style\.css(\?v=[^"]*)?"', f'href="/style.css?v={ASSET_VERSION}"', s)
        s = re.sub(r'src="/site\.js(\?v=[^"]*)?"', f'src="/site.js?v={ASSET_VERSION}"', s)
        f.write_text(s)
        print("built", f.relative_to(ROOT))


if __name__ == "__main__":
    build()
