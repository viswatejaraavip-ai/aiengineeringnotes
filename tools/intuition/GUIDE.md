# Writing the intuition fragment for a pattern

One file per pattern: `tools/intuition/<pattern-id>.html`. It is an HTML *fragment* (no `<html>`, no `<h2>`);
`tools/build_dsa.py` inserts it under the heading "The intuition" at the top of the pattern's page, before the
one-line idea, the walk-through steps and the Google problems. Facts about the pattern come from
`tools/dsa_patterns.json` (idea, invariant, cue, example, steps, problems).

## Who it is for

A 10th-class student who knows arithmetic, a little algebra, and has never seen the data structure.
Write as if explaining across a table with pen and paper. Short sentences. Everyday words first, the technical
word second ("a stack, which is a pile you can only add to or take from the top").

## Shape (use these `<h3>` headings, in this order; drop one only if it truly has nothing to say)

1. `<h3>Start with what you would do by hand</h3>` — a concrete tiny example (numbers ≤ 2 digits, ≤ 8 items),
   the obvious way a person would solve it, and *where that gets slow or messy*. Count the work if it helps
   ("that is 8 × 7 = 56 comparisons for 8 numbers; for a million numbers it is about 500 billion").
2. `<h3>Build the structure, one piece at a time</h3>` — introduce the data structure progressively:
   what it stores, the one or two operations it supports, then the extra rule this pattern adds
   (e.g. "keep it sorted", "only keep candidates that can still win"). Show the structure's contents after each of
   the first few steps on the same tiny example, as a small table or an ordered list. Each step adds exactly one
   new idea. Never present the finished structure first.
3. `<h3>Why it is correct</h3>` — the invariant in plain words, then the one-sentence argument for why each
   step keeps it true. If a claim needs maths, write it: a small equation in `<p class="formula">…</p>`,
   an inequality, a counting argument, a sum. Use `<var>n</var>`, `<sup>`, `<sub>`; no LaTeX.
4. `<h3>Why it is fast</h3>` — derive the complexity, do not just state it ("each index is pushed once and popped
   at most once, so at most 2<var>n</var> stack operations, which is O(<var>n</var>)"). Compare with the by-hand cost.
5. `<h3>How to recognise it in an interview</h3>` — two or three cues in the wording of a problem, and the first
   thing to say out loud. Name one or two of the Google problems from the data file and say in one line how the
   pattern maps onto each.

## Rules

- 400–800 words. Every claim must be true for the algorithm as written in the walk-through steps.
- The example may be the video's example or a smaller one; if different, say so.
- Allowed tags: `<p> <h3> <ol> <ul> <li> <strong> <em> <var> <sup> <sub> <code> <br>`, a table wrapped as
  `<div class="table-wrap"><table>…</table></div>`, `<p class="formula">`, and one optional
  `<div class="concept"><span class="label">…</span><p>…</p></div>` for the key picture. No scripts, no styles,
  no images, no links except to other `/dsa/<id>/` pages.
- Escape `<`, `>` and `&` in text as `&lt;` `&gt;` `&amp;`.
- No filler ("in this section we will…"), no emoji, no exclamation marks.
- Check the fragment parses: `python3 tools/intuition/check.py <pattern-id>` must print OK.
