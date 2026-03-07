# Gradescope Online Assignment Guide

**Status: CANONICAL. BINDING.**

These conventions govern Gradescope Online Assignments authored for courses
using this workflow. They exist to produce consistent, copy-pasteable question
specs that work correctly with Gradescope's auto-grading and manual rubric
features.

---

## 1. Assignment Setup

- **Type:** Online Assignment (not PDF assignment).
- **Submission:** one per pair; partners enter both names in Q1.
- **Q1** is always the Names question — 10 pts, completion-graded,
  free points for submitting with both names.
- Enable **whitespace trimming** in assignment settings whenever any
  Short Answer question is auto-graded.

---

## 2. Question Types

### Short Answer

Use for single-value answers that can be auto-graded by exact match.

- Student sees a small text input box.
- Gradescope compares the submission to the answer key exactly
  (modulo whitespace trimming if enabled).
- For numeric answers that may have rounding variation, Gradescope supports
  a tolerance syntax in the answer key: `=value+-tolerance`
  (e.g., `=8260+-5` accepts any answer from 8255 to 8265). Use this when
  floating-point or rounding differences are possible; omit it when the
  answer must be exact (counts, identifiers).
- Use for: counts, sums, numeric results, short identifiers.

### Free Response

Use for open-ended answers that require a manual rubric.

- Student sees a paragraph text area.
- Graded by the instructor or TA against a rubric.
- Use for: trace steps, pseudocode, explanations, reflections.

---

## 3. Points

- **All questions and subquestions are 10 pts.**
- This allows partial credit across the rubric bands (0 / 4 / 6 / 8 / 10).
- Never use question point values other than 10 without explicit approval.

---

## 4. Answer Region Syntax

Embed the answer region directly in the **Problem field** text.
This makes the spec self-documenting and copy-pasteable into Gradescope.

### Short Answer — with a fixed answer

Place inline at the end of the problem text:

```
How many events does the reducer produce for (Boston, Dancing Plague)? [____](2)
```

The value in parentheses is the exact auto-grade answer.

### Short Answer — completion-graded (no fixed answer)

Place inline at the end of the problem text, no parentheses:

```
Enter both partners' names, separated by a comma. (First Last, First Last) [____]
```

### Free Response

Place on its own line after the problem text:

```
Name one MapReduce pain point that Spark removes.

|____|
```

---

## 5. Question Structure

Each question has exactly two fields:

- **Title field:** the display title (short, noun phrase).
- **Problem field:** the full question text including the answer region.

Never duplicate the title in the problem text.
The title field and problem field serve different roles — keep them distinct.

---

## 6. Subquestions

Use subquestions whenever a question has more than one answer.
Never put two answers in a single question.

- The **parent question** has a title field and an optional problem field
  (use it for shared setup text or instructions; leave blank if not needed).
- The parent question carries **no points** — scoring comes entirely from
  subquestions.
- Each **subquestion** has its own title field (can be blank) and its own
  problem field with an answer region.
- Each subquestion is worth 10 pts.

Example parent:

```
Title field: Reducer Output
Problem field: Answer each subquestion. For population totals, enter whole
numbers with no commas (e.g., 8260 not 8,260).
```

Example subquestion:

```
Title field: (leave blank)
Problem field: What is the total Affected Population for Boston?
(Task B — sum by city) [____](8260)
```

---

## 7. Prohibited Patterns

- **No `>` blockquotes** in problem fields — they do not paste cleanly
  into Gradescope's text editor.
- **No arrows** (`->`, `=>`) in key-value format examples.
  Use a colon instead: `(City, Condition): 1`
- **No two answers in one question.**
  If a question has two answers, split into subquestions.
- **No custom point values** other than 10 per question/subquestion.

---

## 8. Rubric Bands (Free Response)

Standard 5-band rubric for Free Response questions:

| Score | Meaning |
|-------|---------|
| 10 | Correct, complete, explicit |
| 8 | Minor error or format issue |
| 6 | Right direction but vague or partially wrong |
| 4 | Correct logic but significant gaps |
| 0 | Missing, wrong task, or trivially wrong |

Adjust band labels to fit the specific question.
Always include an **Answer key** or **Acceptable answers** list
in the spec for grader reference.

---

## 9. Spec File Format

Each Gradescope assignment lives in its own file alongside the lecture file.
Naming: `lec-##-<slug>-gradescope.md`

The file contains:

1. **Header block** — assignment type, total points, submission rule.
2. **Assignment Description** — paste into the Gradescope description field;
   students see this above all questions.
3. **One section per question** — title field, problem field, type, points,
   rubric (Free Response only), answer key.
4. **Point Summary table** — question, type, pts for every question
   and subquestion.

The lecture file contains only a short pointer to the Gradescope spec file.
Do not duplicate question content in the lecture file.
