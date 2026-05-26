# Canonical Markdown Authoring Rules for GenAI Agents

**Status: CANONICAL. BINDING. NON-NEGOTIABLE.**

These rules govern **all Markdown authored or modified by GenAI agents**.
They exist to optimize for:
- clean git diffs
- long-term maintainability
- human review
- minimal merge conflicts

Style preferences are not optional here; they are operational requirements.

---

## 1. Line Wrapping (HARD RULE)

- Wrap prose at **80 characters** per line.
- Never exceed **90 characters** under any circumstances.

This applies to:
- paragraphs
- list items
- blockquotes

Do NOT rely on editors to reflow text automatically.

---

## 2. One Sentence Per Line (ABSOLUTE)

- Each sentence MUST start on its own line.
- A sentence may wrap to multiple lines due to the 80-character rule.
- Do NOT place multiple sentences on the same line.

This rule exists solely to make git diffs readable and intentional.

Example (correct):

This is the first sentence.  
This is the second sentence, which may wrap  
to a second line if needed.

Example (incorrect):

This is the first sentence. This is the second sentence on the same line.

---

## 3. Paragraph Structure

- Separate paragraphs with **exactly one blank line**.
- Do NOT use multiple blank lines for spacing.
- Do NOT rely on trailing spaces for formatting.

---

## 4. Headings

- Use ATX headings only (`#`, `##`, `###`).
- Leave **one blank line** after a heading.
- Do NOT skip heading levels.
- Headings should be short, declarative, and free of punctuation.

---

## 5. Lists

### Unordered lists
- Use `-` (dash) only.
- One space after the dash.
- Wrap list items using hanging indentation.

### Ordered lists
- Use `1.` for all items (let Markdown auto-number).
- Do NOT manually increment numbers.

---

## 6. Emphasis and Formatting

- Use `**bold**` for emphasis.
- Avoid italics unless meaningfully necessary.
- Avoid inline code for prose emphasis.
- Avoid excessive formatting.

Formatting is a tool, not decoration.

---

## 7. Code Blocks

- Use fenced code blocks with triple backticks.
- Specify a language where possible.
- Do NOT wrap Markdown inside code blocks unless explicitly required.
- Do NOT nest code blocks.

---

## 8. Links

- Use descriptive link text.
- Avoid bare URLs in prose.
- Prefer relative links for in-repo files.
- Keep links on their own line if they would otherwise exceed line length.

---

## 9. Tables

- Use tables sparingly.
- Prefer lists unless tabular comparison is essential.
- Keep table rows readable in raw Markdown.

---

## 10. Front Matter

- Do NOT add YAML front matter unless explicitly requested.
- Do NOT invent metadata fields.

---

## 11. Markdown Is Not a Typesetting Language

- Do NOT optimize for rendered appearance.
- Optimize for:
  - diff clarity
  - semantic structure
  - editability

Rendered formatting is secondary.

---

## 12. Prohibited Behaviors

- Do NOT reflow existing content unless instructed.
- Do NOT “clean up” formatting opportunistically.
- Do NOT mix style changes with content changes in the same commit.

---

## 13. Failure Mode Reminder

The most common failures are:
- long unwrapped lines
- multiple sentences per line
- drive-by formatting changes
- diff-hostile rewrites

When in doubt:
**STOP AND ASK.**
