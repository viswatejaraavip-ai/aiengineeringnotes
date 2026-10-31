#!/usr/bin/env python3
"""Validate intuition fragments: well-formed, allowed tags only, word count in range.
   python3 tools/intuition/check.py <id> [...]    (no args = all)"""
import os, re, sys
from html.parser import HTMLParser
HERE = os.path.dirname(os.path.abspath(__file__))
ALLOWED = {"a", "p", "h3", "ol", "ul", "li", "strong", "em", "var", "sup", "sub", "code", "br", "div", "span", "table", "tr", "th", "td", "thead", "tbody"}
VOID = {"br"}
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack = []; self.errors = []; self.text = []
    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED: self.errors.append(f"tag <{tag}> not allowed")
        if tag == "div" and dict(attrs).get("class") not in ("table-wrap", "concept"): self.errors.append("div must be table-wrap or concept")
        if tag not in VOID: self.stack.append(tag)
    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag: self.errors.append(f"unbalanced </{tag}> (open: {self.stack[-3:]})")
        else: self.stack.pop()
    def handle_data(self, d): self.text.append(d)
def check(id):
    f = os.path.join(HERE, id + ".html")
    if not os.path.exists(f): return f"{id}: MISSING"
    s = open(f).read()
    p = P(); p.feed(s)
    errs = list(p.errors)
    if p.stack: errs.append(f"unclosed {p.stack}")
    if "<h2" in s or "<html" in s or "<script" in s or "<style" in s: errs.append("no h2/html/script/style")
    words = len(" ".join(p.text).split())
    if not 350 <= words <= 900: errs.append(f"{words} words (want 400-800)")
    h3 = len(re.findall(r"<h3", s))
    if h3 < 4: errs.append(f"only {h3} h3 headings")
    if re.search(r"[^&]<(?![/a-zA-Z!])", s) or "!" in re.sub(r"<[^>]+>", "", s).replace("!=", ""): errs.append("stray '<' or an exclamation mark")
    return f"{id}: OK ({words} words)" if not errs else f"{id}: FAIL " + "; ".join(errs)
ids = sys.argv[1:] or sorted(f[:-5] for f in os.listdir(HERE) if f.endswith(".html"))
bad = 0
for id in ids:
    r = check(id); print(r); bad += "FAIL" in r or "MISSING" in r
sys.exit(1 if bad else 0)
