# Course Commons Operating Guide

This repository owns production versions of reusable course guidance and
shared course assets.

## Authority and Scope

The operator owns course policy and pedagogical decisions.
Course projects own their local experiments and course-specific rules.
This repository reviews proposals for reusable course lenses and forges.
It owns and maintains each accepted production component.

Do not move course-specific policy into this repository.
Do not require a proposing course to finish production work before review.
This repository is public.
Do not add private paths, student data, credentials, or private working notes.

## Review a Promotion Proposal

Require the proposal to include:

- the component or diff;
- evidence from real course use;
- the behavior that is reusable;
- each course-specific assumption;
- known limits and failure cases.

Ask for missing evidence before you decide.
Review the proposal for use outside its source course.
Separate reusable behavior from course-specific policy.

For a lens, check these qualities:

- its scope is explicit;
- its evidence requirements are explicit;
- it produces consistent judgments;
- its expected output is clear.

For a forge, check these qualities:

- its inputs and outputs are explicit;
- another course can reproduce its result;
- its allowed effects and permissions are explicit;
- its failure behavior is clear;
- its validation and dependencies are documented.

Accept, request revisions, or reject the proposal.
State the reason for the decision.
When you accept a component, add its production definition to this repository.
Record compatibility, migration requirements, and revisit conditions.

## Lifecycle Boundary

An accepted production component can differ from the source experiment.
The source course can continue its experiment after promotion.
A later course change does not change production until this repository accepts
a new promotion proposal.

Distribution scope does not determine ownership.
A component can be available to all courses while this repository remains its
owner.
