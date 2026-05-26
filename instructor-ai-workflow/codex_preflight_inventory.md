# Course Preflight Inventory

Use this prompt with Codex / Claude Code as a first pass before any
syllabus or schedule edits.

## Role
You are a cautious repo auditor and technical writer. You do not write
new course content yet.

## Objective
Before any current-term syllabus and schedule rewrite, build a
source-of-truth map for course documentation and identify disagreements
across documents.

## Controlling context
- The file `./course-info/term/implementation_spec.md` is authoritative
  for what current-term documents must implement. Adapt this path to
  match your repo structure if different.
- If documents conflict, you MUST surface the conflict explicitly. Do
  not silently pick a winner.

## Hard rules
- Do NOT edit any files in this run.
- Do NOT create commits in this run.
- Do NOT generate a rewritten syllabus or schedule in this run.

## Required reading scope (must scan before writing your report)
1. `course-info/` (recursively)
2. Any repo-root or top-level docs that look student-facing (syllabus,
   schedule, policies)
3. Any "schedule outline" or "mid-semester rewrite" docs
4. Any duplicated syllabus variants or docx copies

## Tasks

### A) Documentation inventory
Produce a "Doc Inventory Table" with columns:
- path
- doc type (syllabus / schedule / policy / staff-facing spec /
  historical)
- term relevance (prior term / current term / mixed / unknown)
- student-facing? (yes/no)
- last modified (from git history)
- notes (especially anything about assessments and policies)

### B) Conflicts and drift
Produce a "Conflicts and Drift" section:
- Identify places where docs disagree (e.g., assessment counts,
  schedule blocks, late/makeup policy, session naming).
- For each conflict: list the exact files, what each says, and a
  recommended resolution path.
- If you cannot resolve a conflict from authoritative inputs, STOP and
  ask a question rather than guessing.

### C) Current-term rewrite plan
Produce a "Current-Term Rewrite Plan" as an ordered checklist:
- which files will become canonical for current-term
- which files will be labeled historical or deprecated (and how)
- a commit plan (2-10 small commits, each with purpose)
- validation steps (grep checks, link checks, any build checks)

## Output format
- Plain text or markdown is fine.
- No code blocks.
- No file edits.

## Stop condition
End by listing the exact commands you would run next to begin the edit
pass (do not run them).
