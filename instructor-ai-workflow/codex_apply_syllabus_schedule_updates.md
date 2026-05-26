# Course Syllabus + Schedule Update

Use this prompt with Codex / Claude Code after running the preflight
inventory pass.

## Role
You are a careful repo editor. You must use small commits and never do
sweeping changes.

## Objective
Implement the current-term document updates that conform to the
controlling implementation spec for this course.

## Preconditions (hard gate)
- You have already completed the preflight inventory pass and produced:
  - a Doc Inventory Table
  - a Conflicts and Drift map
  - a current-term Rewrite Plan
- If you have not done this, STOP and run the preflight prompt instead.

## Hard rules
- Create a new branch for all work (no direct commits to
  `main`/`master`).
- Make small, reviewable commits grouped by intent (one theme per
  commit).
- Use `git mv` for file moves/renames and `git rm` for deletions.
- Do NOT rewrite history (no rebase of shared branches, no
  force-push).
- Do NOT introduce untracked files unless explicitly required; if you
  do, list them.
- Do NOT invent new assignments, assessments, or policies beyond what
  the implementation spec authorizes.
- If multiple docs disagree about student-facing behavior and the spec
  does not resolve it, STOP and ask.

## Required reading scope (must re-check before editing)
1. The controlling implementation spec for the current term
2. The current canonical syllabus and schedule docs identified in the
   preflight plan
3. Any docs that are in conflict per the preflight report

## Implementation targets (minimum)

### 1) Canonicalization
- Establish ONE canonical current-term syllabus source.
- Establish ONE canonical current-term schedule source.
- Any other variants must be clearly labeled historical/deprecated
  (in-file header) and/or moved to an archive location via `git mv`.

### 2) Syllabus updates
Update the canonical syllabus to implement the spec, including:
- assessment structure
- late/makeup policy language
- session type definitions (lecture, discussion, lab, office hours)
- GenAI policy language
- any renamed touchpoints or assessment types

### 3) Schedule updates
Update the canonical schedule to implement the spec's schedule
blueprint, including explicit purpose of each session type per week
and mapping to learning modules where applicable.

### 4) Cross-document consistency
Ensure terminology and policy language match across:
- syllabus
- schedule
- any standalone policy docs in `course-info/`

## Deliverables
- Updated canonical syllabus file(s)
- Updated canonical schedule file
- A short `course-info/term/README.md` that states:
  - what the canonical docs are
  - what is historical/deprecated
  - where to find the implementation spec

## Workflow (required)
1. Print a short plan:
   - branch name
   - files to edit
   - commit plan (2-10 commits)
   - any risky operations
2. Implement changes with incremental commits.
3. Run a grep-based sanity check to confirm key policy phrases are
   present where expected.
4. Provide an end-of-run summary:
   - branch name
   - commit list
   - files changed
   - move/rename map
   - remaining TODOs/questions

## Stop condition
If you hit any ambiguity that would change student-facing behavior,
STOP and ask before proceeding.
