# Canonical Git Hygiene Rules for GenAI Agents

**Status: CANONICAL. BINDING. NON-NEGOTIABLE.**

These rules apply to **any GenAI agent** (Codex, Claude Code, ChatGPT agents, etc.)
that is allowed to modify a git repository.

They are intentionally strict to prevent silent damage, review collapse, and
unrecoverable mistakes.

---

## 1. Branching Rules (MANDATORY)

- You MUST create a new branch for all work.
- You MUST NOT commit directly to `main`, `master`, or any protected branch.
- Branch names should reflect intent, e.g.:
  - `s26-schedule-draft`
  - `otter-lab03-fix`
  - `lms-packaging-week04`

If you are unsure which branch to base from, STOP and ask.

---

## 2. Commit Scope Rules (ABSOLUTE)

- Commits MUST be **small, coherent, and reviewable**.
- Each commit MUST represent **one logical change**.
- You MUST NOT mix unrelated changes in a single commit.

Examples:
- ✅ “Add Week 4 schedule skeleton”
- ✅ “Fix Otter tests for Lab 03”
- ❌ “Update schedule and tweak labs and rename files”

If a change cannot be described clearly in one sentence, it is too large.

---

## 3. Staging Rules (ZERO TOLERANCE)

- **DO NOT use `git add -A`**
- **DO NOT use `git add .`**

You MUST explicitly stage files:
- `git add path/to/file1 path/to/file2`

If you are unsure which files should be staged, STOP and ask.

---

## 4. File Operations (REQUIRED)

- Use `git mv` for renames and moves.
- Use `git rm` for deletions.
- DO NOT delete files without git history.
- DO NOT overwrite source material without preserving a recovery path.

Bulk moves or renames MUST be called out explicitly in the plan.

---

## 5. History Integrity (NON-NEGOTIABLE)

- DO NOT rewrite shared history.
- DO NOT force-push.
- DO NOT rebase shared branches.
- DO NOT squash commits unless explicitly instructed.

Linear history is less important than recoverability.

---

## 6. Plan-First Requirement

Before making *any* file changes, you MUST output:
- target branch name
- files to be edited
- commit plan (list of commits with intent)
- any risky operations

No edits are permitted until this plan is shown.

---

## 7. End-of-Run Reporting

At the end of the run, you MUST report:
- branch name
- list of commits (one-line summaries)
- files changed
- any TODOs or uncertainties

---

## 8. Failure Mode Reminder

The most common agent git failures are:
- over-staging
- oversized commits
- silent refactors
- accidental deletions

When in doubt:
**STOP AND ASK.**
