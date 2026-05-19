# Notebook Assignment Guide

**Status: CANONICAL.**

This document covers the standard pattern for producing Jupyter notebook
assignments that use Otter Grader, shared support files, and a reproducible
distribution workflow.

Adapt the examples to the course's actual repo layout.

---

## 1. Overview

Notebook assignments in this workflow typically:

- use Otter Grader DSL for grading
- include shared support files through symlinks or copies
- distribute through a course-specific delivery platform
- submit through the platform the course has chosen

Keep the notebook itself as the course-facing artifact.

Keep shared infrastructure in one maintained location.

---

## 2. File Organization

Assignment directories should contain:

- the notebook
- links or copies of shared support files
- assignment-specific assets
- optional prior-art references

Typical pattern:

```text
<assignment-dir>/
├── assignment.ipynb
├── assignment-config.yaml
├── helpful-script.sh
├── error-helper.py
├── error-config.json
└── prior-art/
```

If the assignment uses shared datasets, keep those in a standard repo-level
location and link or copy them into the assignment directory.

Build output should go to a generated directory outside the source tree when
possible.

---

## 3. Required Components

### Otter Config

If the course uses a shared config file, reference it from the first raw cell:

```text
# ASSIGNMENT CONFIG
config_file: assignment-config.yaml
```

If the notebook overrides `files:` or `requirements:`, list the full
replacement set.

Do not include `points_possible`.

### Question Structure

Use the Otter question and solution structure from `otter-dsl.md`.

### Error Handling Files

If the course maintains helper files for friendlier student error messages,
include them consistently in every notebook assignment.

### Requirements Block

Always declare packages that the notebook imports.

Do not assume a package that works locally will exist in the grading
environment.

---

## 4. Writing Style In Student-Facing Notebooks

Do not include:

- assistant-style preambles like `I'll help you`
- emojis unless the course already uses them intentionally
- time estimates in student-visible prompts
- overly complex output formatting in beginner-facing code

Prefer:

- direct instructions
- numbered steps when sequence matters
- brief hints when the task is conceptually hard
- simple visible code

Student-visible code should avoid formatting tricks that distract from the
actual concept.

Good:

```python
print("Estimated probability:", round(estimated_prob, 3))
```

Less good for novice-facing material:

```python
print(f"Estimated probability: {estimated_prob:.3f}")
```

For full prose guidance, use `writing-voice-guide.md`.

---

## 5. Build Workflow

1. Create the assignment directory.
1. Add shared support files.
1. Add any datasets or local assets.
1. Build the notebook.
1. Validate the notebook structure.
1. Execute the notebook before generating the student version.
1. Run the course's Otter build wrapper if one exists.
1. Inspect the generated student output.

If the repo includes a wrapper that dereferences symlinks before running
`otter assign`, use it instead of raw `otter assign`.

---

## 6. Validation Checklist

- All questions have proper begin and end markers.
- The config points to the intended shared file.
- Shared file links resolve correctly.
- Test cells return booleans.
- Student-facing text avoids AI signals and unnecessary decoration.
- The notebook executes cleanly before packaging.

---

## 7. Deployment Caveat

Do not assume every course deploys notebooks the same way.

If the target environment matters for setup, save checkpoints, or packaging,
confirm whether the course uses local Jupyter, Codespaces, JupyterHub, or
another platform before finalizing the workflow.
