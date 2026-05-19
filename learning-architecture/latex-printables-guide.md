# LaTeX Printable Materials Guide

**Status: CANONICAL. BINDING.**

This document governs how agents produce print-ready student-facing
materials.

---

## 1. Content vs Print Rendering

Markdown is the canonical format for content:

- design docs
- TA keys
- rubrics
- instructor notes
- lab guides

LaTeX is a print rendering format.

Use it only when the instructor wants a physical artifact students will print
or hold:

- answer sheets
- handouts
- question cards
- other print-ready materials

The `.tex` file is an output artifact, not the source of truth.

---

## 2. Workflow

1. Keep the content in Markdown or derive it from Markdown source files.
1. Typeset that content into a `.tex` file when a printable version is
   requested.
1. Compile the `.tex` file to PDF.

---

## 3. Page Setup

Use `article` with `letterpaper` and reasonable margins:

```latex
\documentclass[11pt,letterpaper]{article}
\usepackage[margin=1in]{geometry}
```

Suppress page numbers for single-use handouts:

```latex
\pagestyle{empty}
```

---

## 4. Fonts

All printable documents should use one of these setups.

### Option A

```latex
\usepackage{fontspec}
\setmainfont{Open Sans}
```

### Option B

```latex
\usepackage{fontspec}
\setmainfont{Red Hat Text}
\newfontfamily\headingfont{Red Hat Display}
```

If no preference is specified, use Open Sans.

These fonts require LuaLaTeX or XeLaTeX, not pdfLaTeX.

Compile with:

```bash
lualatex -shell-escape <filename>.tex
```

If compilation fails, report the error.

Do not claim the PDF is correct without compiling it.

---

## 5. Code Listings

Use `minted` when code snippets are part of the printable document:

```latex
\usepackage{minted}
```

If `minted` is unavailable, fall back to `listings`:

```latex
\usepackage{listings}
\lstset{
  language=Python,
  basicstyle=\ttfamily,
  breaklines=true,
  frame=single
}
```

---

## 6. Headings And Helpers

Use `titlesec` for section formatting:

```latex
\usepackage{titlesec}
\titleformat{\section}{\Large\bfseries}{}{0em}{}
\titlespacing*{\section}{0pt}{1.5em}{0.5em}
```

Useful helpers for fill-in-the-blank layouts:

```latex
\usepackage{parskip}
\usepackage{underscore}

\newcommand{\blankline}{%
  \noindent\rule{\linewidth}{0.4pt}}

\newcommand{\shortblank}{\rule{8em}{0.4pt}}
```

Example name header:

```latex
\noindent Name: \rule{14em}{0.4pt}
\hfill ID: \rule{8em}{0.4pt}
```

---

## 7. Layout Patterns

### Answer Sheets

- One section per question.
- Use `\shortblank` for short answers.
- Use `\blankline` plus vertical space for open responses.

### Handouts

- Include a name or ID header when needed.
- Leave generous write-in space.
- Use visible separators for stations or parts.

### Question Cards

- Use a grid or two-column layout.
- Keep each card self-contained.
- Separate cards clearly for cutting.

---

## 8. Filename Convention

Use lowercase, hyphenated names that match the surrounding course naming
scheme.

Examples:

- `lec-05-verification-answer-sheet.tex`
- `lab-05-handout.tex`
- `lab-05-question-cards.tex`

---

## 9. What Not To Do

- Do not produce LaTeX for TA keys, rubrics, or instructor-only docs.
- Do not treat `.tex` as the source of truth.
- Do not use pdfLaTeX when custom fonts are specified.
- Do not omit the font setup.
- Do not invent layout patterns without a clear reason.
