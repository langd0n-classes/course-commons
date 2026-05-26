# Lecture Prep: Source Deck Review and Lecture Overview

## Purpose

Use this prompt to build a lecture overview for an upcoming lecture by
consulting semester-scoped source deck exports.
The output is a completed or partially completed lecture `.md` file in the
appropriate folder for your course structure.

> **Note:** The semester branch itself is the canonical record of what was
> delivered. Keep lecture exports in the lecture folder they belong to.

---

## Source deck file locations

Within a semester branch, slide exports live in the lecture folder they
support:

```
lms/{lm-folder}/lec-{NN}-{slug}/
  lec-{NN}-{slug}.md
  lec-{NN}-{delivered-title-slug}.pdf
  lec-{NN}-{delivered-title-slug}.txt
  {YYYYMMDD}-Outline.md   # optional slide-title index
```

This is a delivery record first and future prior-art second.
If you want to inspect an older semester, check out that semester branch and
open the relevant lecture folder there.

If the same lecture is exported more than once, keep only the most current
canonical export files.
Do not keep duplicate copies or "copy" variants.

---

## Handling the slide boundary problem

TXT exports from Google Slides contain **no slide boundary markers** — the text
runs continuously. To identify slide breaks:

1. **Prefer the PDF** for slide number reference. Each page = one slide.
   Open or read the PDF to count pages and identify slide titles visually.
2. **In the TXT**, treat these as slide boundaries:
   - A short, title-case or ALL-CAPS line standing alone (no trailing punctuation)
   - A line that matches a section heading in the corresponding PDF
3. **Reference slides by title, not line number.** Write "What to lift" entries
   as `{DeckCode}.pdf slide N — "{Slide Title}"` so the reference is verifiable.
   Avoid "lines 5–51" style references — they are fragile and hard to verify.

If an `{YYYYMMDD}-Outline.md` index exists in the lecture folder, use it as the
authoritative slide-title-to-number mapping.

---

## How to read source-deck TXT files

1. Read the TXT file for the relevant deck.
2. Identify slide groups using the boundary rules above.
3. For each slide group, note:
   - The slide title (bold or standalone short line)
   - The key bullet points or body text
4. Skip: URL-only slides, "Announcements" slides, and "Attendance" slides.
5. Do not copy old slide content verbatim — adapt framing, update examples,
   and flag anything that no longer applies.

---

## Lecture file format

Lecture files live at `lms/{lm-folder}/lec-{NN}-{slug}.md`.
Use this template:

```markdown
# Lecture {NN}: {Title}

## Purpose

{1–3 sentences on what this lecture accomplishes and why it belongs here
in the course arc.}

## Learning targets

- {Verb + measurable outcome}
- {Verb + measurable outcome}

## Skills targeted in this meeting

- {Skill code} {Skill description}

## Prep required of students

- {What students should have done or read before class}

## In-class plan (time-blocked)

- 0 to {N} min. {Block title}.
  What to lift:
  - `lec-{NN}-{delivered-title-slug}.pdf` slide {N} — "{Slide Title}"
  - `lec-{NN}-{delivered-title-slug}.pdf` slides {N} to {M} — "{Title range}"
- {N} to {M} min. {Block title}.
  What to lift:
  - {source reference or "new — build from scratch"}

## Instructor materials needed

- {Slides, notebooks, worksheets, etc.}

## Existing materials to reuse

- {Paths to related existing files in the repo}

## Source Deck

- **Original Google Slides title:** {exact deck title}
- **Local export:** `lec-{NN}-{delivered-title-slug}.pdf`
- **Text export:** `lec-{NN}-{delivered-title-slug}.txt`

**Slides used:** {list or range}
**Slides skipped:** {list or range, or "none"}

## Delivery Divergence

**Planned:** {planned lecture concept, if different}
**Delivered:** {actual delivered lecture concept}
**Why it diverged:** {brief explanation, or "none"}
**Implication for next lecture(s):** {what lec-NN+1 / lec-NN+2 should
account for}
**Next-term note:** {adopt this drift, refine it, or pull back}

## New materials required

- {What needs to be built}

## Release or due triggers (if any)

- {Any GAIE, assignment, or assessment gated on this lecture}

## Notes after teaching (leave blank)
```

---

## Step-by-step instructions

1. **Identify the lecture** — title, number, learning module, and date from
   the course schedule.
2. **Find source decks** — locate the relevant exported deck(s) in the lecture
   folder.
   If none exists yet, note that in "New materials required" and draft from
   the learning targets alone.
3. **Scan the TXT** for relevant content using the boundary rules above.
   Identify which slide groups map to each planned in-class block.
4. **Draft the lecture file** using the template above. Fill in all fields;
   use `{TBD}` only for things that genuinely cannot be inferred.
5. **Write "What to lift" entries** using PDF slide numbers, not TXT line
   ranges. Example:
   ```
   `lec-16-statistical-inference.pdf`
   slides 3 to 6 — "Variability of the Estimate", "Quantifying Uncertainty"
   — adapt framing, drop the census/no-census decision tree
   ```
6. **Record both planned and delivered identity.**
   The lecture folder name and markdown filename stay tied to the planned
   lecture slot.
   Exported deck filenames reflect the delivered lecture title.
   If they diverge materially, fill in the `## Delivery Divergence` section.
7. **Do not rename the lecture folder or markdown file just because delivery
   drifted.**
   Drift should remain visible for follow-on lecture planning.
8. **Do not overwrite existing lecture files without checking whether the old
   version contains design rationale or after-teaching notes that need to be
   preserved.**
