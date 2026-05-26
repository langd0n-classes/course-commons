# Slide Content Guide for DS-100

Slides are built in Google Slides. Claude produces slide content as
structured markdown files; the instructor copies content into Google Slides.

---

## Slide content file format

Each slide is one block. Use this structure exactly:

```
## Slide: Title text here

**Bullets:**
- Short bullet (≤ 6 words)
- Another short bullet
- One more

> **Speaker notes:** Full sentences here. Can be as long as needed.
> Describe what to say, what to ask the class, and what to do next.
```

Rules:
- `## Slide:` is the heading level for every slide — one per block.
- Bullets are stage-readable: **6 words maximum per bullet**.
  If it takes more than 6 words, it belongs in speaker notes.
- Speaker notes use `>` blockquote lines. These are for the instructor,
  not students. Include Socratic questions, transitions, and timing cues.
- Do NOT use `>` blockquotes for any other purpose in slide files —
  they are reserved for speaker notes.

---

## Supplementary content blocks

For slides that need a data table, column list, code snippet, or reference
values, add a clearly labelled block after the bullets:

```
## Slide: Feature Engineering — Pair Activity

**Bullets:**
- 7 minutes, work in pairs
- Propose 2 features from BlueBikes columns
- Compute r, submit in Gradescope

**Reference values:**
r(distance, tripduration) ≈ 0.56  ·  r(hour, tripduration) ≈ 0.02

> **Speaker notes:** Keep this slide up the whole 7 minutes.
> Call on 3 pairs after time is up.
```

---

## Where slide content lives

Slide content is a `## Slides` section inside the lecture plan file
(`lec-##-<slug>.md`), not a separate file. All `## Slide:` blocks
go at the end of that file, after the staff notes.

Do not create standalone `*-slide.md` files.

---

## Constraints

- No emoji in bullet text.
- No f-string format specs or inline rounding in code snippets
  (same rule as notebooks — see notebook-assignment-guide.md).
- No AI writing signals ("Let's explore…", "In this slide…").
- Bullets are fragments, not sentences — no ending periods.
- Speaker notes are full sentences.
