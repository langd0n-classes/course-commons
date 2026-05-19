# Gradescope Online Assignment Guide

**Status: CANONICAL. BINDING.**

These conventions govern Gradescope Online Assignments authored for courses
using this workflow.

They exist to produce consistent, copy-pasteable question specs that work
correctly with Gradescope's auto-grading and manual rubric features.

Course-local copies should point back to this file and stay in sync.

---

## 1. Assignment Setup

- Type: Online Assignment, not PDF assignment.
- Submission: one per pair when pair submission is used.
- Q1 is the names question when partner names are required.
- Use 10 points and completion grading for the names question.
- Enable whitespace trimming whenever any Short Answer question is
  auto-graded.

---

## 2. Question Types

### Short Answer

Use for single-value answers that can be auto-graded by exact match.

- Students see a small text input box.
- Gradescope compares the submission to the answer key exactly, modulo
  whitespace trimming when enabled.
- For numeric answers with rounding variation, Gradescope supports tolerance
  syntax in the answer key: `=value+-tolerance`.
- Use this when floating-point or rounding differences are possible.
- Omit it when the answer must be exact.

Use cases:

- counts
- sums
- numeric results
- short identifiers

### Free Response

Use for open-ended answers that require a manual rubric.

- Students see a paragraph text area.
- Graders score the response against a rubric.

Use cases:

- trace steps
- pseudocode
- explanations
- reflections

---

## 3. Points

- All questions and subquestions are 10 points.
- This supports partial credit across the rubric bands.
- Do not use other point values without explicit approval.

---

## 4. Answer Region Syntax

Embed the answer region directly in the Problem field text.

This keeps the spec self-documenting and easy to paste into Gradescope.

### Short Answer With A Fixed Answer

Place the answer region inline at the end of the problem text:

```text
How many events does the reducer produce for this input? [____](2)
```

The value in parentheses is the exact auto-grade answer.

### Short Answer For Completion Only

Place the answer region inline with no answer in parentheses:

```text
Enter both partners' names, separated by a comma. [____]
```

### Free Response

Place the answer region on its own line after the problem text:

```text
Name one pain point this tool removes.

|____|
```

---

## 5. Question Structure

Each question has exactly two fields:

- Title field: short display title
- Problem field: full prompt text including the answer region

Do not duplicate the title inside the problem text.

---

## 6. Subquestions

Use subquestions whenever a question has more than one answer.

Do not put two answers in a single question.

- The parent question may contain shared setup text or instructions.
- The parent question carries no points.
- Each subquestion has its own problem field and answer region.
- Each subquestion is worth 10 points.

Example parent:

```text
Title field: Reducer Output
Problem field: Answer each subquestion. Enter whole numbers with no commas.
```

Example subquestion:

```text
Title field: (leave blank)
Problem field: What is the total affected population for Boston? [____](8260)
```

---

## 7. Prohibited Patterns

- No `>` blockquotes in problem fields.
- No arrows like `->` or `=>` in key-value examples.
- No two answers in one question.
- No custom point values other than 10 per question or subquestion.

Use a colon instead of arrows:

```text
(City, Condition): 1
```

---

## 8. Rubric Bands

Standard five-band rubric for Free Response questions:

| Score | Meaning |
|-------|---------|
| 10 | Correct, complete, explicit |
| 8 | Minor error or format issue |
| 6 | Right direction but vague or partially wrong |
| 4 | Correct logic but significant gaps |
| 0 | Missing, wrong task, or trivially wrong |

Adjust the band labels to fit the specific question.

Always include an answer key or acceptable answers list for grader reference.

---

## 9. Spec File Format

Each Gradescope assignment should live in its own file alongside the session
or assignment materials.

Suggested naming:

```text
lec-##-<slug>-gradescope.md
```

The file should contain:

1. Header block with assignment type, total points, and submission rule.
1. Assignment description for the Gradescope description field.
1. One section per question with title, problem field, type, points, rubric,
   and answer key as needed.
1. Point summary table for every question and subquestion.

If another file holds the primary teaching materials, keep only a short
pointer there.

Do not duplicate full question content across files.
