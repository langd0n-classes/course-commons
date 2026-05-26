# AI Course Projects — Setup Guide

Two AI project configurations for course design and consistency
checking. Set them up once per course; use them all term.

- `project_design_studio.md` — exploration and design thinking
- `project_stewardship.md` — consistency checking against your
  controlling documents

These are complementary, not alternatives. Design Studio is for
open-ended thinking before decisions are made. Stewardship is for
checking whether a draft or change is consistent with what you've
already decided.

---

## Before you start: prepare your files

Both projects need your course documents attached. AI projects work
best with plain text — not PDFs, not Word docs.

**Convert everything to Markdown or plain text before uploading.**

PDFs are often parsed poorly (garbled tables, missing structure).
Word docs lose formatting on import. A `.md` or `.txt` file gives
the AI clean, reliable access to your content.

If you only have a PDF or Word doc: open it, select all, paste into
a text editor, save as `.md`, clean up the formatting minimally.
Twenty minutes of prep pays off all term.

### Recommended files to attach

**Minimum viable set (both projects):**
- Your current-term syllabus
- Your current-term schedule or course calendar
- Your academic calendar for the term

**Strongly recommended:**
- A course conventions or standards document (naming, file
  organization, session types)
- Your pedagogical framework or design principles
- An implementation spec or controlling doc for the current term,
  if you maintain one

**For Design Studio only (optional but useful):**
- Assessment patterns or rubric reference
- Content templates
- Prior-term redesign notes or design briefs

**For Stewardship only (optional but useful):**
- Agent or AI rules for your course repo (if you have one)
- Any standalone policy documents (late work, GenAI, academic
  conduct)

If a file is missing, the project will tell you what it cannot
evaluate. That's intentional — it's better than the AI guessing.

---

## Setting up a ChatGPT Project

1. Go to [chatgpt.com](https://chatgpt.com) and sign in.
2. In the left sidebar, click **Projects** → **New project**.
3. Name the project (e.g. "DS-100 Design Studio" or
   "DS-100 Stewardship").
4. Click **Customize ChatGPT** (or the project settings gear).
5. In the **Instructions** field, paste the full contents of the
   relevant prompt file (`project_design_studio.md` or
   `project_stewardship.md`).
6. Under **Files**, upload your prepared course documents.
7. Save. Start a new conversation inside the project.

**Note:** Files attached to a ChatGPT Project persist across
conversations in that project. You don't need to re-upload each
session.

---

## Setting up a Claude Project

1. Go to [claude.ai](https://claude.ai) and sign in.
2. Click **Projects** in the left sidebar → **New project**.
3. Name the project.
4. In the project **Instructions** field, paste the full contents
   of the relevant prompt file.
5. Under **Project knowledge**, upload your prepared course
   documents.
6. Save. Start a new conversation inside the project.

**Note:** Claude Projects also persist files and instructions across
conversations. The project knowledge is available in every
conversation you start inside it.

---

## Which to use when

| Situation | Use |
|---|---|
| Thinking through a redesign | Design Studio |
| Exploring tradeoffs before deciding | Design Studio |
| Reacting to student feedback | Design Studio |
| Checking a draft syllabus for consistency | Stewardship |
| Verifying a schedule change doesn't break anything | Stewardship |
| Sharing a "check your work" tool with a TA | Stewardship |

Keep them separate. Don't use Design Studio to enforce constraints
and don't use Stewardship to brainstorm — they have different
operating modes and mixing them degrades both.

---

## Updating files mid-term

If your syllabus or schedule changes during the term, re-upload the
updated file to both projects. Delete the old version first to avoid
the AI referencing stale content.
