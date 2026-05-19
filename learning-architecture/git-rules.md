# Canonical Git Hygiene Rules for GenAI Agents

**Status: CANONICAL. BINDING. NON-NEGOTIABLE.**

These rules apply to any GenAI agent allowed to modify a git repository.

They are intentionally strict to prevent silent damage, review collapse,
and unrecoverable mistakes.

---

## 1. Branching Rules

- You MUST create a new branch for all work.
- You MUST NOT commit directly to `main`, `master`, or any protected branch.
- Branch names should reflect intent.

Examples:

- `s26-schedule-draft`
- `otter-lab03-fix`
- `lms-packaging-week04`

If you are unsure which branch to base from, stop and ask.

---

## 2. Commit Scope Rules

- Commits MUST be small, coherent, and reviewable.
- Each commit MUST represent one logical change.
- You MUST NOT mix unrelated changes in a single commit.

Examples:

- `Add Week 4 schedule skeleton`
- `Fix Otter tests for Lab 03`
- Not `Update schedule and tweak labs and rename files`

If a change cannot be described clearly in one sentence, it is too large.

---

## 3. Staging Rules

- Do NOT use `git add -A`.
- Do NOT use `git add .`.

You MUST explicitly stage files:

```bash
git add path/to/file1 path/to/file2
```

If you are unsure which files should be staged, stop and ask.

---

## 4. File Operations

- Use `git mv` for renames and moves.
- Use `git rm` for deletions.
- Do NOT delete files without preserving git history.
- Do NOT overwrite source material without a recovery path.

Bulk moves or renames MUST be called out explicitly in the plan.

---

## 5. History Integrity

- Do NOT rewrite shared history.
- Do NOT force-push.
- Do NOT rebase shared branches.
- Do NOT squash commits unless explicitly instructed.

Linear history matters less than recoverability.

---

## 6. Plan-First Requirement

Before making any file changes, output:

- target branch name
- files to be edited
- commit plan with intent
- any risky operations

No edits are permitted until this plan is shown.

---

## 7. End-of-Run Reporting

At the end of the run, report:

- branch name
- list of commits with one-line summaries
- files changed
- any TODOs or uncertainties

---

## 8. Failure Mode Reminder

The most common agent git failures are:

- over-staging
- oversized commits
- silent refactors
- accidental deletions

When in doubt, stop and ask.
