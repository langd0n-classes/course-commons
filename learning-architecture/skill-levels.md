# Skill Levels: I / P / A

## The framework

Skills and topics are tracked across three coverage levels, representing how
deeply a skill is engaged at any given point in the course:

| Level | Name | Meaning |
|---|---|---|
| **I** | Introduced | Covered in lecture; explained and contextualized. Students encounter the concept for the first time. |
| **P** | Practiced | Hands-on in a class activity, lab, studio, or exercise. Students work with the concept actively. |
| **A** | Assessed | Incorporated in a homework, project deliverable, or formal evaluation. Students are accountable for the skill. |

## How levels combine

A skill can pass through multiple levels in a single session or across several
sessions over the semester:

- `I` only — awareness target; students should recognize the concept, not master it
- `I + P` — students encounter and work with it, but are not formally evaluated
- `I + P + A` — full mastery target; introduced, practiced, and then assessed

Not every skill reaches A. Some topics are intentionally I-only or I+P
(perspective topics, context-setting, future-course scaffolding).

## Flow through the semester

The mental model: skills are horizontal lines flowing left to right through the
semester. Sessions are the nodes they pass through. The I → P → A progression
is the expected direction of travel — a skill should not be assessed before it
has been introduced and practiced.

When a session is canceled (snow day, illness), some lines break. The impact
is visible as skills that were scheduled to move from I to P, or P to A, that
now have a gap.

## How to declare levels in course files

In lecture, lab, and hw files, declare topics and their intended coverage level
in the `## Topics (Planned)` section:

```markdown
## Topics (Planned)

- `#16` ETL vs. ELT — definition and decision criteria  (I + P)
- `#17` Idempotent load patterns                        (I)
- `#18` Pipeline failure modes and retry strategy       (I + P + A)
```

After delivery, update the course topics tracker with the confirmed session.

## Relationship to the Learning Arc

I / P / A maps onto the Learning Arc verbs:

| I/P/A | Learning Arc phase |
|---|---|
| I | Explore / Introduce |
| P | Consolidate / Practice |
| A | Verify / Assess |

See `course-design-principles.md` for the full Learning Arc description.
