# Lecture Stub Guide

**Status: CANONICAL.**

Use this guide when drafting a lecture stub from prior-semester materials.

Course-specific prompt variants should live in
`course-info/course-prompt-materials/`.

This file describes the reusable pattern only.

---

## 1. Purpose

The goal is to build a lecture stub or overview for an upcoming session by
consulting prior-semester slide decks and related notes.

The output should be a partially or fully completed Markdown lecture file that
captures:

- the purpose of the session
- the skills targeted
- the in-class blocks
- which prior-art slides to reuse or adapt
- what must be built from scratch

---

## 2. Prior-Art Sources

Prior-semester slide content often lives on older branches or in separate
worktrees, not in the current working branch.

The working branch should stay clean.

Use prior-art materials as references, not as files to move into the current
tree.

Search by topic, not by lecture number alone.

Module names, lecture numbers, and deck titles often drift across terms.

---

## 3. Core Workflow

1. Identify the lecture title, date, module or unit, and role in the course.
1. Find prior-art decks or notes that match the topic.
1. Read the prior-art text export or per-slide content.
1. Determine which prior slides are still useful.
1. Record what to lift, what to adapt, and what to build new.
1. Draft the lecture stub in the current term's file structure.
1. Verify that the stub matches current naming and content conventions.

---

## 4. Getting Exact Slide References

Do not invent slide numbers.

If the plain-text export lacks slide boundaries, use the PDF one page at a
time or generate a slide index from the PDF.

Reference prior art by exact slide number and title where possible.

Good:

```text
S26-L01 slides 6-14 - "What is data science?" through "Exploration"
```

Less good:

```text
Use the middle section of the old intro deck.
```

If a deck-level outline file exists, treat it as the authoritative index.

---

## 5. What To Lift

For each block of the lecture, decide which prior-art content falls into one
of these buckets:

- reuse with minimal edits
- adapt for updated framing, examples, or logistics
- drop because it is outdated
- rebuild from scratch

Do not copy older material verbatim without checking whether terminology,
timing, examples, or course sequencing have changed.

Skip announcement slides, attendance slides, and dead logistics.

---

## 6. Recommended Stub Structure

Include:

- title
- session metadata
- purpose
- skills targeted
- prep required of students
- prior-art source table
- time-blocked in-class plan
- materials needed
- release or due triggers
- notes after teaching

Within each in-class block, record:

- what happens
- why it belongs there
- what to lift from prior art
- what is new

---

## 7. Verification Before Finalizing

Check:

- file path and naming match course conventions
- prior-art references use real slide numbers
- old logistics and dates are removed
- current course terminology is used consistently
- new material is called out explicitly

If no useful prior art exists, say so directly and draft from the learning
targets instead.
