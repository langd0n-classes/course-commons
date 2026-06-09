# Build a Prior-Art Map (course-agnostic template)

You are a build agent. Your job is to do, **once and centrally**, the aggressive
prior-art search that downstream lecture-build agents otherwise do badly (or
skip). You produce a single, greppable **prior-art map**: for each teaching
topic, the prior slide/notebook material from *every* reviewed term that teaches
it, with the teaching move named and the page resolved.

The map exists so a downstream agent building a lecture can `grep` its topic,
read one bounded slice, and find several ready variants to crib from — instead
of re-searching the file tree and settling for whatever it finds first.

This is a **reusable template.** Everything course-specific lives in the Inputs
block, which the operator supplies per course (usually via a small course-local
invocation file that points back to this template). Do not hard-code course
names, terms, or machine paths into this file.

---

## Inputs (supplied per course)

The invocation must provide all of these. If any is missing or empty, **stop and
report** — do not guess paths.

- **Repo path** — root under which the course's prior terms can be read, e.g.
  `~/loc-areas/courses/<course>/`
- **Content index / TOC** — the index that maps topics/decks to files.
- **Topic seed** — the canonical, term-free topic list (with stable IDs) that
  defines the map's topic anchors.
- **Reviewed prior terms** — enumerate them *from the TOC itself*: every prior
  term that appears in the index, recent and old. Do **not** restrict to the
  most recent term. Missing the older terms is the exact failure this map fixes.
- **Output map path** — where to write the produced map.

---

## Required reading

1. The TOC — your entry point to every prior deck. Treat its paths as hints;
   verify by opening the actual file.
2. The topic seed — the stable topic list and its IDs. These IDs are your topic
   anchors.
3. The course's LM/organization guide, in particular any "prior art" rules and
   the principle that **a prior item is reusable by teaching shape, not just by
   matching content or syntax.** That principle is the lens for the whole job:
   you are cataloguing *teaching moves*, not matching datasets or APIs.

---

## What "teaching move" means (the crux)

A teaching move is *what the slide/cell does pedagogically*, independent of
dataset or API. Examples, all topic-neutral:

- "Predict the output before running the cell."
- "Read the result aloud before interpreting it."
- "State the honest claim, then state what the chart cannot claim."
- "Introduce the operation on a tiny hand-built toy example first."
- "Show the broken version on purpose, then the repair."

The same move recurs across terms under different data and different syntax. A
demo in one library and a demo in another are the **same move** if both walk the
same pedagogical steps. Record the move so a downstream agent sees the prior
material as reusable even when every line of code differs.

---

## Method

For each topic in the seed list:

1. **Search the TOC across ALL reviewed terms** for that concept. If the topic
   seed provides a `keywords:` line for this topic, use it as your starting
   search terms (and extend as you learn the corpus vocabulary). Otherwise,
   derive search terms **specific to this topic** — the concept word and its
   real synonyms and code tokens (for a joins topic: `join`, `merge`, `pivot`,
   `grouping`, `key column`, `left table`). Do **not** reuse a generic keyword
   set across topics; that is how dedicated decks get missed. Then **also sweep
   filenames and deck titles**: a deck literally named `…grouping-pivots-joins`
   is a candidate for a joins topic even if its body text does not keyword-match.
   Collect every candidate from every term — not the first hit.
2. **Resolve each candidate to a real slide/cell, and capture its full span.**
   Slides typically come as `.txt`/`.pdf` pairs in the same directory: grep the
   `.txt` for the title/phrase, then confirm in the `.pdf` the **first and last**
   page the move occupies — a teaching move usually runs across several
   consecutive slides, and a downstream agent needs both bounds to lift the whole
   thing, not just where it starts. In a headless run without native PDF
   rendering, resolve the bounds by extracting per-page text — e.g.
   `pdftotext -f N -l N file.pdf -` walking pages, or `pypdf` page iteration — and
   match the opening and closing slides. For notebook-anchored older terms, cite
   the notebook and the cell/section range instead of pages.
3. **Name the teaching move** that slide/cell embodies (see above). One or two
   sentences. This is the load-bearing field.
4. **Note what to adapt** for reuse (swap dataset, translate API, retitle).
5. **Deduplicate honestly.** If the same move appears near-identically across
   terms, list each term's entry but mark the later ones `variant-of: <term>`
   so a reader sees "one move reused" — not "several different approaches." Only
   present entries as distinct options when the teaching move genuinely differs.

Write all entries for a topic together, grouped **topic-major, term-minor** —
every term's variant colocated under the one topic anchor.

---

## Output format (locked — do not improvise)

A single markdown file at the output path. Line-oriented so a downstream agent
can `grep -n` for its topic, find the enclosing `=====` anchors, and `Read` only
that slice — never loading the whole file. Do **not** use JSON/XML: a partial
slice of those is unusable; a partial slice of this is still readable.

Start the file with this consumption header verbatim (fill `<COURSE>`):

```
# Prior-Art Map — <COURSE>

How to use this file (for build agents):
1. grep -n "TOPIC: <your-topic>" prior-art-map.md   → get the line number.
2. Read from that line to the next "=====" line — that slice is your topic.
3. The slice lists every reviewed term's variant of this teaching move.
   Review them ALL and pick the strongest teaching shape — do not take the
   first. Entries marked `variant-of:` are copies, not separate options.
4. Each entry is a reuse candidate. Cite it in your segment guide as
   [LIFT — <term>-<deck> slides A-B ("<title>")] — give the full slide span,
   not just the first slide.
```

Then one block per topic:

```
===== TOPIC: scatter-plots =====
seed-id: <topic-id-from-seed>
keywords: scatter, association, two numerical variables, correlation preview

- term:  <term>
  deck:  <deck name>
  file:  <path to .txt or .ipynb>
  page-start: <first slide/page of the move>
  page-end:   <last slide/page of the move>
  move:  Introduce scatter as "do two numbers move together?"; each point is one
         observation; name direction/strength/clusters/outliers before
         interpreting.
  adapt: <what to change for reuse>

- term:  <older term>
  deck:  <deck name>
  file:  <path>
  page-start: <first slide/page of the move>
  page-end:   <last slide/page of the move>
  move:  <the teaching move>
  adapt: <what to change>
  variant-of: <term>   # include only if near-identical to another entry

===== TOPIC: bar-charts =====
...
```

Field rules:

- `seed-id` — the topic's ID from the seed list. Omit only if the topic has no
  seed entry; note that.
- `keywords` — alternate search terms **specific to this topic** so an agent
  that greps a synonym still lands here. Derive them from the topic itself;
  never copy a generic set across topics (a copied keyword line is a sign the
  topic was not really searched, and dedicated decks will have been missed).
- `term`, `deck`, `file`, `page-start`, `page-end`, `move`, `adapt` — required
  on every entry. Always give **both** bounds — the first and last slide of the
  move — never just the opening slide. For a move that genuinely lives on one
  slide, set them equal.
- `variant-of` — optional; present only for near-duplicate reuses.
- Never invent a page number. If you cannot confirm a bound, write
  `page-end: UNVERIFIED` (or `page-start: UNVERIFIED`) and say why in `adapt`.

---

## Topic granularity

- Seed the topic list from the canonical topics file. One anchor per distinct
  teaching target.
- **Split** a topic when it carries several genuinely distinct moves (e.g. split
  "joins" into `join-mental-model`, `join-syntax`, `join-sanity-checks` if the
  prior decks teach those as separate moves).
- **Do not** split so finely that an agent can't guess the anchor name. When in
  doubt, keep the topic and list the moves as separate entries inside it.

---

## Coverage expectations

- Every reviewed term that covers a topic should appear under that topic. A
  topic block that only ever cites the most recent term is a red flag that the
  older terms were not searched — go back and search them.
- A topic may legitimately have a single entry, or none. An empty result must
  show the search that produced it: `# no prior art found — searched: <terms/keywords>`.
  Never leave silence.

---

## Guardrails

- Read-only on all prior-term material. Do not edit, fix, or reformat prior
  decks to match current conventions.
- The map is a reference over frozen prior terms — it does not track the current
  term's in-progress files.
- Do not resolve pages by guessing from the `.txt` alone; confirm against the
  `.pdf` (or the notebook cell).

---

## Verification

- Run `git status --short` in the repo that holds the output map.
- Report: topics covered, total entries, and the **per-term entry counts** (this
  is how the operator confirms older terms were actually searched).
- List any topics with no prior art and the searches that came up empty.
- Do not commit. Do not push.

---

## Reusing this template

Create a small course-local invocation that fills the **Inputs** block (repo
path, TOC, topic seed, reviewed terms, output path) and points the agent here
for the methodology. The methodology, format, and consumption header are
course-neutral. The produced map is meant to be shareable: any build agent that
can `grep` and `Read` can consume it without loading the whole file.
