# Otter Grader DSL Guide

**Status: CANONICAL.**

This document provides working guidance for creating or editing Otter Grader
assignments in Jupyter notebooks.

Always check the official Otter documentation for the latest syntax and
features:

- Main docs: <https://otter-grader.readthedocs.io/en/latest/>
- Otter Assign:
  <https://otter-grader.readthedocs.io/en/latest/otter_assign/>
- Tutorial: <https://otter-grader.readthedocs.io/en/latest/tutorial.html>

---

## 1. Assignment Config

Typical first-cell structure:

```text
# ASSIGNMENT CONFIG
init_cell: true
export_cell: false
solutions_pdf: false
template_pdf: false
generate:
    show_stdout: true
    filtering: true
    pagebreaks: true
    zips: false
```

Do not include `points_possible`.

Otter calculates it automatically.

---

## 2. Question Structure

Each question should follow this sequence:

1. Raw cell with `# BEGIN QUESTION` metadata.
1. Markdown cell with the prompt.
1. Raw cell with `# BEGIN SOLUTION`.
1. Code cell containing the prompt and solution markers.
1. Raw cell with `# END SOLUTION`.
1. Raw `# BEGIN TESTS` cell for auto-graded questions.
1. One or more code test cells.
1. Raw `# END TESTS` cell.
1. Raw `# END QUESTION` cell.

Example metadata:

```text
# BEGIN QUESTION
name: q1_part1
points: 10
manual: false
```

Example solution cell:

```python
""" # BEGIN PROMPT
# Student instructions here
result = ...
""" # END PROMPT
# BEGIN SOLUTION NO PROMPT
result = 42
# END SOLUTION
```

Both in-cell markers are required.

---

## 3. Tests

- Use one test per code cell.
- Tests must return booleans.
- Do not use assertions.

Good pattern:

```python
try:
    my_function()
    True
except Exception:
    False
```

---

## 4. Lecture Notebook Notes

For lecture demos, wrap each section in a question block even if nothing is
graded.

This preserves markdown context in the student notebook.

- Use `manual: true`.
- Omit test blocks for non-graded sections.
- Avoid setting `points:` unless the notebook is genuinely graded.

For instructor-only notes, use a `remove` tag on cells that should be stripped
from the distributed student version.

---

## 5. Prompt Writing Rules

- Do not use triple-quoted docstrings inside prompt content.
- Use regular comments instead.
- Keep student-visible code simple and readable.
- Prefer direct instructions over assistant-style narration.

---

## 6. Common Mistakes

- including `points_possible`
- using assertions in tests
- placing multiple tests in one cell
- using markdown cells for DSL markers
- forgetting solution markers inside the code cell
