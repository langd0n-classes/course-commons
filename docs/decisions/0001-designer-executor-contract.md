# ADR-0001: A shared designer→executor contract for course-building agents

- **Status:** proposed
- **Date:** 2026-05-29
- **Deciders:** Langdon White (architecture sounding-board: Mimir)
- **Attribution:** AI-C (Collaborative) — AI-drafted, human-directed and iterated across revisions. See https://langd0n.com/ai-attribution

## Terms

- **Designer** — the role that decides *what* to build and *why* (a human, or a judgment-focused agent).
- **Executor** — the agent that *builds* the artifact from a spec.
- **Contract** — the interface between them: required *inputs* to start, and a *definition-of-done* to finish.
- **Attribution tier** — the AI-A/E/C/G level declared for an artifact (see https://langd0n.com/ai-attribution), setting the human involvement required before it ships.

## Context

Course materials are built by AI agents working from per-course prompt corpora — one well-developed exemplar, others earlier-stage. These corpora predate reusable agent tooling (skills, subagents), so shared structure across courses was never factored out.

As more courses and workshops adopt the same agent-built workflow, each corpus risks independently re-implementing the same build-and-review logic, which drifts.

An AI attribution taxonomy already exists. Today it is used informally to *size expected human effort* (closer to planning-poker than to an enforced step) — not as a gate in any pipeline.

**Scope:** this ADR decides only the *handoff contract* between a designer and an executor, and how a course extends it. It does **not** design the designer or executor agents themselves (deferred — see Consequences).

## Options considered

1. **Each course re-declares the full build/review policy** — maximum flexibility; the logic is duplicated N times and drifts.
2. **One rigid shared policy, inherited verbatim** — DRY, but a course cannot legitimately differ (e.g. add a precondition another course lacks).
3. **Shared base contract + per-course extensions** *(chosen)* — each course may *extend* a shared base with additional requirements; the executor must satisfy the full (base + extensions) contract before starting and before reporting done.

## Decision

- course-commons defines a **base designer→executor contract**: the required inputs an executor needs to *begin*, and a **definition-of-done** it must meet to *finish*. The base is shared by all courses.
- A course may **add requirements** to either side (extra required inputs, e.g. "fetch the schedule first"; or extra done-criteria). Courses *extend*; they do not fork the base.
- The executor **may not begin** until all required inputs (base + course) are present, and **may not report done** until all done-criteria (base + course) are met. Missing requirements **fail closed**.
- **Attribution tier is one field of the contract.** On input, an artifact carries a declared tier; on output, one done-criterion is "the human involvement the tier requires has occurred." If an artifact type declares **no** tier, it defaults to the **highest** tier — review required. Silence means high-stakes, not low.

## Why

- Shared base + per-course extensions dissolves the duplication-vs-rigidity trade-off (Option 1 vs Option 2): courses share the common part and add only what is genuinely local. This is the standard interface-plus-extension shape.
- Encoding the contract as a precondition (before) and a definition-of-done (after) makes "is it done?" objective rather than a per-artifact judgment call — the same reason build systems and test suites make done-ness explicit. Attribution tier is the worked example of a single criterion living on both sides: declared as a required input, verified as a done-criterion.
- Defaulting an undeclared tier to "review required" is chosen because the expensive failure is *silently shipping unreviewed student-facing material*; a missing declaration should over-ask, never under-ask.

**Revisit triggers:**

1. *(highest risk)* If default-to-review produces enough low-value prompts that the human starts rubber-stamping, the gate is decorative — retune per-artifact-type defaults before the habit sets in.
2. If the **shared-base + per-course-extension** split stops holding — courses need to differ in the *base*, not just extend it — the core claim is wrong; re-examine the seam.
3. When the designer/executor agents are actually built (deferred), their real interface may force changes here; supersede then.

## Consequences

- *(easy)* Onboarding a new course or workshop = supply its extensions, not a new policy. Local additions stay local.
- *(cost)* The base contract and the attribution vocabulary must be authored and maintained in course-commons; courses must keep their extensions conformant (a validation chore).
- *(deferred)* The designer/executor agent design — including whether multiple judgment-focused partner agents share a common role, and the principle that design judgment and mechanical compliance are distinct roles that should not be collapsed into one regime — is out of scope here and recorded separately. Build order: (1) wire attribution into the done-check of the existing publish pipeline; (2) build the first executor against this contract; (3) revisit shared abstractions once two or more real instances exist.
