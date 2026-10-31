#!/usr/bin/env python3
"""Generate the Data structures & algorithms section from tools/dsa_patterns.json:

  /dsa/index.html           the section home (marker layout; build_site.py fills the listing)
  /dsa/<pattern-id>/index.html   one note per pattern: video, idea, invariant, walk-through steps, Google problems

Run, then run tools/build_site.py.
"""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "tools" / "dsa_patterns.json").read_text())
VIDEO_BASE = "/dsa/videos"
DATE = "31 Oct 2026"
SITE = "https://aiengineeringnotes.com"

# How the 27 topic groups fold into sidebar sections (order = reading order).
SECTIONS = [
    ("arrays", "Arrays and strings", ["Arrays & Hashing", "Prefix Sums", "Two Pointers", "Sliding Window", "String Algorithms"]),
    ("stacks", "Stacks and queues", ["Stack", "Monotonic Stack", "Queue & Deque"]),
    ("search", "Searching and sorting", ["Binary Search", "Sorting", "Intervals"]),
    ("lists", "Linked lists and design", ["Linked List", "Design"]),
    ("trees", "Trees, heaps and tries", ["Trees", "Binary Search Tree", "Heap", "Trie"]),
    ("graphs", "Graphs", ["Graphs"]),
    ("dp", "Recursion, DP and greedy", ["Backtracking", "Dynamic Programming", "Greedy"]),
    ("math", "Math, bits and matrices", ["Bit Manipulation", "Math", "Matrix"]),
    ("advanced", "Advanced structures and simulation", ["Advanced Structures", "Interactive", "Simulation"]),
]
TOPIC_DESC = {
    "Arrays & Hashing": "Answering questions about an array in one pass by remembering what you have already seen.",
    "Prefix Sums": "Precompute running totals so any range becomes a subtraction.",
    "Two Pointers": "Two indices that move with purpose so the whole array is covered in one pass.",
    "Sliding Window": "A contiguous range that grows and shrinks while a running aggregate stays exact.",
    "String Algorithms": "Matching, hashing, parsing and rebuilding strings without quadratic rescans.",
    "Stack": "Last in, first out: matching, nesting, expression evaluation and collision simulation.",
    "Monotonic Stack": "A stack kept sorted so each element learns its nearest greater or smaller neighbour in amortised O(1).",
    "Queue & Deque": "First in, first out, and the deque that keeps only useful candidates.",
    "Binary Search": "Halving a sorted range, a monotone predicate, or the answer space itself.",
    "Sorting": "Sorting as a preprocessing step, and the partition and merge ideas behind it.",
    "Intervals": "Sort by start or end, then sweep.",
    "Linked List": "Pointer surgery with fast and slow runners, dummy heads and in-place reversal.",
    "Design": "Composing a hash map with a list, a heap or a sorted structure to hit the required big-O per operation.",
    "Trees": "Recursion that returns something upward, level-order traversal, and trees treated as graphs.",
    "Binary Search Tree": "Ordering gives you bounds, inorder gives you sorted order.",
    "Heap": "A priority queue for the k best, two halves, k-way merges and scheduling.",
    "Trie": "A tree of characters (or bits) for prefix and XOR queries.",
    "Graphs": "Traversal, ordering, connectivity and shortest paths on explicit and implicit graphs.",
    "Backtracking": "Build a candidate one choice at a time and undo on return.",
    "Dynamic Programming": "Define the state, write the transition, pick the order to fill it.",
    "Greedy": "Commit to the locally best choice when an exchange argument proves it safe.",
    "Bit Manipulation": "XOR, masks and the lowest set bit.",
    "Math": "Number theory, digits, fast exponentiation, randomness and coordinate geometry.",
    "Matrix": "Traversal orders and searches that use a matrix's structure.",
    "Advanced Structures": "Segment trees, Fenwick trees, ordered sets, bucketing and meet in the middle.",
    "Interactive": "Problems where you query an oracle and must minimise the number of questions.",
    "Simulation": "Model the rules exactly with the smallest state that decides the next step.",
}


def esc(s):
    return html.escape(str(s), quote=True)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def accent(s):
    """*word* → <em>word</em>"""
    parts = s.split("*")
    return "".join(f"<em>{esc(p)}</em>" if i % 2 else esc(p) for i, p in enumerate(parts))


def dur(sec):
    return f"{int(round(sec))} s" if sec < 60 else f"{int(sec // 60)} min {int(round(sec % 60))} s"


PATS = DATA["patterns"]
BY_GROUP = {}
for p in PATS:
    BY_GROUP.setdefault(p["group"], []).append(p)


def page_path(p):
    return f"/dsa/{p['id']}/"


def nav_structure():
    """What build_site.py needs: sections > topics > one unnamed group of pages."""
    out = []
    for sid, title, groups in SECTIONS:
        topics = []
        for g in groups:
            pages = [{"path": page_path(p), "title": f"{p['number']:03d} · {p['name']}", "sub": p["idea"],
                      "meta": f"{DATE} · {dur(p['duration'])} video"} for p in BY_GROUP.get(g, [])]
            topics.append({"id": "dsa-" + slug(g), "title": g, "desc": TOPIC_DESC.get(g, ""),
                           "groups": [{"title": "", "pages": pages}]})
        out.append({"id": "dsa-" + sid, "title": title, "topics": topics})
    return out


SHELL = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} · AI Engineering Notes</title>
  <meta name="description" content="{desc}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{site}{path}">
  <link rel="canonical" href="{site}{path}">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/style.css?v=4">
</head>
<body>
<div class="wrap">

  <!-- site:header --><!-- /site:header -->

  <div class="layout">
  <aside class="sidenav" id="sidenav" aria-label="All notes">
    <!-- site:nav --><!-- /site:nav -->
  </aside>
  <main class="content">

{body}

  <nav class="pager" aria-label="Reading order">
    <!-- site:pager --><!-- /site:pager -->
  </nav>

  <footer>
    © 2026 AI Engineering Notes · <a href="/">Home</a> · <a href="https://github.com/viswatejaraavip-ai">GitHub</a>
  </footer>
  </main>
  <aside class="onpage" aria-label="On this page">
    <!-- site:onpage --><!-- /site:onpage -->
  </aside>
  </div>

</div>
<script src="/site.js?v=4"></script>
</body>
</html>
"""


def problems_table(p):
    rows = []
    for q in p["problems"]:
        d = q["difficulty"].title()
        rows.append(f'<tr><td><a href="{esc(q["link"])}">{esc(q["title"])}</a></td>'
                    f'<td><span class="diff {q["difficulty"].lower()}">{d}</span></td>'
                    f'<td class="num">{q["freq"]:.0f}</td><td>{"last 6 months" if q["recent"] else ""}</td></tr>')
    return ('<div class="table-wrap"><table><tr><th>Problem</th><th>Difficulty</th><th class="num">Frequency</th><th>Reported</th></tr>'
            + "".join(rows) + "</table></div>")


def pattern_page(p, prev_p, next_p):
    siblings = [s for s in BY_GROUP[p["group"]] if s["id"] != p["id"]]
    steps = "".join(f"<li>{accent(s)}</li>" for s in p["steps"])
    related = ", ".join(f'<a href="{page_path(s)}">{esc(s["name"])}</a>' for s in siblings) or "none in this topic"
    first = p["problems"][0]["title"] if p["problems"] else ""
    frag = ROOT / "tools" / "intuition" / f"{p['id']}.html"
    if frag.exists():
        intuition = '    <h2 id="intuition"><span class="num">01</span>The intuition</h2>\n' + frag.read_text().strip()
        n_idea, n_walk, n_google, n_related = "02", "03", "04", "05"
    else:
        intuition = ""
        n_idea, n_walk, n_google, n_related = "01", "02", "03", "04"
    desc = f"{p['idea']} Pattern {p['number']} of {len(PATS)} behind Google's DSA interview questions, with a {dur(p['duration'])} walk-through video."
    body = f"""  <p class="crumbs"><!-- site:crumbs --><!-- /site:crumbs --></p>

  <article class="post">
    <header>
      <h1>{esc(p["name"])}</h1>
      <p class="lede">{accent(p["idea"])}</p>
      <div class="byline"><span>Pattern {p["number"]:03d} of {len(PATS)}</span><span>{esc(p["group"])}</span><span>{esc(p["complexity"])}</span><span>{DATE} · {dur(p["duration"])} video</span></div>
    </header>

    <div class="video">
      <video controls preload="none" playsinline poster="/dsa/{p["id"]}/poster.jpg">
        <source src="{VIDEO_BASE}/{p["id"]}.mp4" type="video/mp4">
      </video>
    </div>
    <p class="post-meta">{dur(p["duration"])} · title card, the worked example step by step, then a recap. The captions carry the explanation; there is no narration. <a href="{VIDEO_BASE}/{p["id"]}.mp4">Download the MP4</a>.</p>

    <div class="concept">
      <span class="label">The invariant</span>
      <p>{accent(p["invariant"])}</p>
    </div>

{intuition}

    <h2 id="idea"><span class="num">{n_idea}</span>The idea in one line</h2>
    <p>{accent(p["idea"])}</p>
    <p><strong>Reach for it when:</strong> {esc(p["cue"])}</p>
    <p><strong>Cost:</strong> {esc(p["complexity"])}.</p>

    <h2 id="walkthrough"><span class="num">{n_walk}</span>The walk-through, step by step</h2>
    <p>The video works one example: <strong>{esc(p["example"])}</strong>. These are its captions in order, so you can follow without the video or check a step you missed.</p>
    <ol class="steps">
      {steps}
    </ol>

    <h2 id="google"><span class="num">{n_google}</span>Asked at Google</h2>
    <p>{len(p["problems"])} Google-tagged LeetCode problems use this pattern. Frequency is LeetCode's Google-tag score (higher means reported more often); "last 6 months" marks problems reported in the most recent window of the export.</p>
    {problems_table(p)}

    <h2 id="related"><span class="num">{n_related}</span>Related patterns</h2>
    <p>Other patterns in <a href="/dsa/#dsa-{slug(p["group"])}">{esc(p["group"])}</a>: {related}.</p>
  </article>"""
    return SHELL.format(title=esc(p["name"]), desc=esc(desc), site=SITE, path=page_path(p), body=body)


def home_page():
    n_groups = len(BY_GROUP); n_probs = len({q["slug"] for p in PATS for q in p["problems"]})
    total = sum(p["duration"] for p in PATS)
    body = f"""  <div class="hero">
    <h1>Data structures and algorithms, as patterns.</h1>
    <p class="lede">The {len(PATS)} patterns behind the questions Google asks, each with a short video that runs the real algorithm on one example, step by step.</p>
  </div>

  <section id="how-to-read">
    <h2 id="h-how-to-read">How to read these notes</h2>
    <p>Google's DSA interview questions repeat a small number of ideas. These notes list every one of those ideas as a pattern: a one-line idea, the invariant the code keeps true, when to reach for it, and the Google-tagged LeetCode problems it solves. The source is the public LeetCode company-tag export: 2,324 Google-tagged problems, of which {n_probs} are mapped here across {n_groups} topics.</p>
    <p>Every pattern has a {dur(total / len(PATS))} video on average ({int(total // 60)} minutes in all): a title card, the algorithm run on one small input with a caption per step and the state on screen, then a recap of the invariant, the complexity and the problems. The steps are also written out under each video. Read a topic top to bottom, or search the sidebar for a problem name you have been asked. The sidebar ticks the patterns you have finished, in this browser only.</p>
    <p>Difficulty colours and frequencies come from LeetCode; "last 6 months" marks problems reported in the most recent window of the export.</p>
  </section>

  <!-- site:groups --><!-- /site:groups -->"""
    return SHELL.format(title="Data structures and algorithms", desc="154 DSA patterns behind Google's interview questions, each with a step-by-step video and the Google-tagged LeetCode problems it solves.",
                        site=SITE, path="/dsa/", body=body).replace("<meta property=\"og:type\" content=\"article\">", "<meta property=\"og:type\" content=\"website\">")


def build():
    (ROOT / "dsa").mkdir(exist_ok=True)
    (ROOT / "dsa" / "index.html").write_text(home_page())
    for i, p in enumerate(PATS):
        d = ROOT / "dsa" / p["id"]; d.mkdir(exist_ok=True)
        (d / "index.html").write_text(pattern_page(p, PATS[i - 1] if i else None, PATS[i + 1] if i + 1 < len(PATS) else None))
    print(f"wrote dsa/index.html and {len(PATS)} pattern pages")


if __name__ == "__main__":
    build()
