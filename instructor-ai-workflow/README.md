# Instructor AI Workflow

Reusable prompts and skills for using AI to build and maintain courses.
Focused on the instructor's production workflow — not student-facing AI,
not AI policy.

---

## What's here

### `ai-projects/`
ChatGPT and Claude Project configurations for course design thinking
and consistency checking. Start here if you have no course repo set up
yet. See the README inside for setup instructions and recommended files
to attach.

### Codex / Claude Code skills
For instructors with a course in a git repo:

- `codex_preflight_inventory.md` — audit course documents before any
  term update
- `codex_apply_syllabus_schedule_updates.md` — implement term updates
  safely after the preflight pass

### Content generation prompts
- `slides-guide.md` — generate slide content as structured markdown
  for use in Google Slides
- `stub-generation-prompt.md` — build a lecture overview from prior
  semester source decks

### Agent hygiene
Rules for any AI agent that touches a course repo:
- `README_CANONICAL_GIT_RULES.md`
- `README_CANONICAL_MARKDOWN_RULES.md`
