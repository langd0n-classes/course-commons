## Introduction

In many classes, AI use requires two orthogonal systems. One system is the instructor sharing their expectations of students regarding AI use. In the Spark program, the expectations are set at a broad, general level and get progressively more specific. The other system is how the students communicate AI use back to instructors, their peers, and, in many cases, the public.

## AI Use Expectations

At the broadest level, Boston University (BU) expects students to follow the [Code of Student Responsibilities](https://www.bu.edu/dos/policies/student-responsibilities/) and the [Academic Conduct Code](https://www.bu.edu/academics/policies/academic-conduct-code/), which set the University’s expectations for student conduct and academic integrity. Separately, the Faculty of Computing and Data Sciences (CDS) has adopted the [Generative AI Assistance (GAIA) Policy](https://www.bu.edu/cds-faculty/culture-community/gaia-policy/) for students taking courses within the unit. Spark courses fall within CDS and therefore students are subject to those expectations. At the next, more granular, level, instructors set expectations through statements in the syllabus for the class. These can vary quite widely but the Spark program tries to ensure consistency among them. However, the instructor is ultimately the authority for their class and their syllabus. As a student, be sure you read and understand the expectations outlined by the instructor. Lastly, a given assignment will have an expectation of AI use which is what is outlined below.

## AI-Use Colors

Follow the color stated on the assignment or activity. An assignment-specific rule overrides the general descriptions below.

| Color | Rule |
| :---- | :---- |
| **Green** | AI use is encouraged for all activities such as concept exploration, debugging help, producing content or code, and brainstorming. You remain responsible for every submitted claim and artifact. |
| **Yellow** | AI may explain concepts, help brainstorm, ask questions, or critique work you created. It may not produce content or code that you incorporate into the submission unless the assignment states a specific exception. |
| **Red** | AI use is prohibited for the marked activity. Oral verification, for example, is always Red. |

When AI use is allowed, protect private data, credentials, unpublished team work, and information that you do not have permission to share. You remain responsible for correctness, licensing, privacy, security, and your understanding of everything you submit.

## AI Attribution

Citations identify the sources and authorities that support your work. AI attribution serves a different purpose: it discloses how an AI tool contributed to the work you submit. This policy uses the [AI Attribution model](https://langd0n.com/ai-attribution/), a compact set of levels similar to [Creative Commons](https://creativecommons.org/share-your-work/use-remix/cc-licenses/).

## AI Attribution Levels

Use the [AI Attribution model](https://langd0n.com/ai-attribution/) to describe the contribution, not the assignment’s permission level.

| Level | Name | Use it when |
| :---- | :---- | :---- |
| **AI-N** | None | No generative-AI tool contributed to the submitted artifact. Traditional spell-checkers and other non-generative tools do not count as AI assistance. |
| **AI-A** | Assisted | AI provided suggestions, autocomplete, or lookup; you wrote the work and made the decisions. |
| **AI-E** | Enhanced | AI transformed or improved work that you created; you substantially revised and curated the result. |
| **AI-C** | Collaborative | You and AI jointly developed the substance through iteration; you directed, evaluated, and revised the work. |
| **AI-G** | Generated | AI produced the primary substance of the artifact; you reviewed it and chose to submit it. |

Choose the level that best describes the submitted artifact. The amount of time spent with a tool does not determine the level.

## AI Use Disclosure

Every deliverable must end with an AI use disclosure. Give your name and email, the level and explanation, and the tool. For example:

Student Name \<student@bu.edu\>

AI-C. I used Claude to propose edge cases for the validation function. I ran the cases, rejected one unsafe conversion, and revised the function to return False for invalid input.

Tool: Claude

If you did not use AI, write your name and email followed by:

AI-N.

Do not submit a vague statement such as “AI was used.” The statement must identify what the tool did and what you did to check or change its contribution.

### Source Control Commits

Commit messages should record what changed and include AI attribution and co-author trailers when applicable. Keep each commit focused on one issue or feature; avoid broad staging commands such as git add \-A. For example:

Remove unnecessary pronoun instruction from C00
Keep the name tent focused on preferred names and the distinctive visual cue without introducing an unrelated public-display decision.

AI-Attribution: AI-C (https://langd0n.com/ai-attribution)
Co-authored-by: langdon \<1832177+langdon@users.noreply.github.com\>
Co-Authored-By: ds-551 / GPT-5.6 Sol

---

Langdon White
AI-E. I used Codex to produce an initial draft from materials I had previously written. I substantially rewrote that draft for this context, then used Codex to review clarity, consistency, and mechanics.
Tool: ds-551 / gpt-5.6-sol
