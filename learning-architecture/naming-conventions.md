# Naming Conventions

Conventions for folder and file naming across courses. All courses follow the
same base pattern; course-specific variations are noted.

---

## Base pattern

```
{type}-{##}-{short-slug}
```

- **type** — lowercase prefix identifying the content type (see table below)
- **##** — two-digit zero-padded number (`01`, `02`, ... `27`)
- **short-slug** — lowercase, hyphen-separated words, ≤5 words

The same pattern applies to both the **folder name** and the **primary
markdown file** inside it:

```
lec-08-etl-elt/
  lec-08-etl-elt.md     ← matches the folder name
  assets/
  starter/
```

---

## Content type prefixes

| Prefix | Type | Used in |
|---|---|---|
| `lec` | Lecture | DS-100, DS-551 |
| `lab` | Lab / discussion section | DS-100, DS-551 |
| `hw` | Homework / assignment | DS-551 |
| `gaie` | GenAI Exploration (pre-class) | DS-100 |
| `lm` | Learning module (container) | DS-100 |
| `a` | Assessment / activity (in-class) | DS-100 |

---

## Course-specific structure

### DS-100

Uses a **module-first** layout. Lectures and labs live inside learning module
(`lm-##`) directories:

```
lms/
  lm-01-programming-basics/
    lec-05-programming-basics.md
    lab-02-programming-foundations.md
    gaie-01-programming-concepts.md
    lm-01-overview.md
```

Module directories: `lm-{##}-{slug}/`
Overview files: `lm-{##}-overview.md`

### DS-551

Uses a **flat, type-first** layout. No module container directories:

```
course-content/
  lectures/
    lec-01-intro-to-scalable-data-systems/
    lec-02-apis-and-git-workflow/
  hw/
    hw-01-scraping-and-containers/
  labs/
    lab-01-course-onboarding/
  project/
    phase-1/
    phase-2/
    phase-3/
```

Numbers are course-wide (not per-module) and match the master schedule.

---

## Supporting file layout (inside a session folder)

```
{type}-{##}-{slug}/
  {type}-{##}-{slug}.md    ← primary file, matches folder name
  assets/                  ← images, diagrams
  starter/                 ← student starter code
  solution/                ← instructor-only solution (if present)
  artifacts/               ← student-submitted evidence (rarely in repo)
```

---

## What NOT to do

- Do not use underscores in folder or file names (`lec_08` ✗)
- Do not omit the zero-pad (`lec-8` ✗ → `lec-08` ✓)
- Do not use dates in folder names for recurring content types
  (`lec08-etl-elt-prep-2026-02-12` ✗ → `lec-08-etl-elt` ✓)
- Do not name the primary file `README.md` — name it to match the folder
