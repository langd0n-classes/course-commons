#!/usr/bin/env python3
import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def enable_tab_completion() -> None:
    try:
        import readline  # noqa: F401
    except Exception:
        return
    try:
        readline.parse_and_bind("tab: complete")
    except Exception:
        return


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "#": r"\#",
        "$": r"\$",
        "%": r"\%",
        "&": r"\&",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def add_percent_if_numeric(value: str) -> str:
    if not value:
        return ""
    if "%" in value:
        return value
    try:
        float(value)
    except ValueError:
        return value
    return f"{value}%"


def field(val: str, width: str) -> str:
    if val:
        return r"\makebox[" + width + r"][l]{" + latex_escape(val) + r"}"
    return r"\underline{\hspace{" + width + r"}}"


def inline_field(val: str, width: str) -> str:
    if val:
        return latex_escape(val)
    return r"\underline{\hspace{" + width + r"}}"


def parse_assignments(text: str) -> list[tuple[str, str]]:
    items = []
    due_pat = re.compile(r"\(\s*due\s*:\s*([^)]+)\)", re.IGNORECASE)
    for raw in text.split(";"):
        raw = raw.strip()
        if not raw:
            continue
        match = due_pat.search(raw)
        due = ""
        name = raw
        if match:
            due = match.group(1).strip()
            name = (raw[: match.start()] + raw[match.end() :]).strip()
        name = re.sub(r"\s{2,}", " ", name)
        items.append((name, due))
    return items


def pack_assignments(items: list[tuple[str, str]], max_len: int = 70) -> list[tuple[str, str]]:
    if not items:
        return items
    if any(due for _, due in items):
        return items
    packed = []
    current = ""
    for name, _ in items:
        if not current:
            current = name
            continue
        candidate = f"{current}; {name}"
        if len(candidate) <= max_len:
            current = candidate
        else:
            packed.append((current, ""))
            current = name
    if current:
        packed.append((current, ""))
    return packed


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{label}{suffix}: ").strip()
    return val if val else default


def prompt_yes_no(label: str, default: bool = False) -> bool:
    default_str = "Y/n" if default else "y/N"
    while True:
        val = input(f"{label} [{default_str}]: ").strip().lower()
        if not val:
            return default
        if val in {"y", "yes"}:
            return True
        if val in {"n", "no"}:
            return False


def resolve_logo_path(logo_input: str) -> str:
    logo_input = logo_input.strip()
    if not logo_input:
        return ""
    path = Path(logo_input)
    if path.is_absolute() and path.exists():
        return str(path)
    local_path = Path(__file__).parent / logo_input
    if local_path.exists():
        return str(local_path)
    if path.exists():
        return str(path)
    return ""


def summarize_entries(
    name: str,
    student_id: str,
    email: str,
    address: str,
    cell: str,
    college: str,
    class_year: str,
    course: str,
    section: str,
    sem_year: str,
    instructor: str,
    reason: str,
    percent_complete: str,
    average: str,
    deadline: str,
    final_grade: str,
    items: list[tuple[str, str]],
    logo_name: str,
) -> str:
    lines = [
        "Review entries before generating PDF:",
        f"Name: {name}",
        f"BU ID #: {student_id}",
        f"Address: {address}",
        f"Email: {email}",
        f"Cell Phone #: {cell}",
        f"College: {college}",
        f"Class Year: {class_year}",
        f"Course: {course}",
        f"Section: {section}",
        f"Sem/Year: {sem_year}",
        f"Instructor: {instructor}",
        f"Reason: {reason}",
        f"Percent Complete: {percent_complete}",
        f"Average: {average}",
        f"Overall Deadline: {deadline}",
        f"Final Grade: {final_grade}",
        f"Logo: {logo_name or '(none)'}",
        "Assignments:",
    ]
    if not items:
        lines.append("  (none)")
    else:
        for item, due in items:
            suffix = f" (Due: {due})" if due else ""
            lines.append(f"  - {item}{suffix}")
    return "\n".join(lines)


def edit_loop(
    name: str,
    student_id: str,
    email: str,
    address: str,
    cell: str,
    college: str,
    class_year: str,
    course: str,
    section: str,
    sem_year: str,
    instructor: str,
    reason: str,
    percent_complete: str,
    average: str,
    deadline: str,
    final_grade: str,
    logo_name: str,
    assignment_text: str,
    items: list[tuple[str, str]],
) -> tuple[
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    list[tuple[str, str]],
]:
    fields = [
        ("Name", "name"),
        ("BU ID #", "student_id"),
        ("Address", "address"),
        ("Email", "email"),
        ("Cell Phone #", "cell"),
        ("College", "college"),
        ("Class Year", "class_year"),
        ("Course", "course"),
        ("Section", "section"),
        ("Sem/Year", "sem_year"),
        ("Instructor", "instructor"),
        ("Reason", "reason"),
        ("Percent Complete", "percent_complete"),
        ("Average", "average"),
        ("Overall Deadline", "deadline"),
        ("Final Grade", "final_grade"),
        ("Logo", "logo"),
        ("Assignments", "assignments"),
    ]

    values = {
        "name": name,
        "student_id": student_id,
        "email": email,
        "address": address,
        "cell": cell,
        "college": college,
        "class_year": class_year,
        "course": course,
        "section": section,
        "sem_year": sem_year,
        "instructor": instructor,
        "reason": reason,
        "percent_complete": percent_complete,
        "average": average,
        "deadline": deadline,
        "final_grade": final_grade,
        "logo": logo_name,
        "assignments": assignment_text,
    }

    while True:
        summary = summarize_entries(
            values["name"],
            values["student_id"],
            values["email"],
            values["address"],
            values["cell"],
            values["college"],
            values["class_year"],
            values["course"],
            values["section"],
            values["sem_year"],
            values["instructor"],
            values["reason"],
            values["percent_complete"],
            values["average"],
            values["deadline"],
            values["final_grade"],
            items,
            values["logo"],
        )
        print("\n" + summary + "\n")
        action = input("Generate PDF? [Y]es / [E]dit / [C]ancel: ").strip().lower()
        if action in {"", "y", "yes"}:
            break
        if action in {"c", "cancel"}:
            raise SystemExit("Canceled.")
        if action in {"e", "edit"}:
            print("Select a field to edit:")
            for idx, (label, key) in enumerate(fields, start=1):
                current = values[key]
                if key == "assignments":
                    current = " ".join(item for item, _ in items)
                print(f"{idx}) {label}: {current}")
            choice = input("Field number: ").strip()
            if not choice.isdigit():
                continue
            idx = int(choice)
            if idx < 1 or idx > len(fields):
                continue
            label, key = fields[idx - 1]
            if key == "assignments":
                assignment_text = prompt_assignments()
                items = parse_assignments(assignment_text)
                values[key] = assignment_text
            else:
                values[key] = prompt(label, values[key])
        else:
            continue

    return (
        values["name"],
        values["student_id"],
        values["email"],
        values["address"],
        values["cell"],
        values["college"],
        values["class_year"],
        values["course"],
        values["section"],
        values["sem_year"],
        values["instructor"],
        values["reason"],
        values["percent_complete"],
        values["average"],
        values["deadline"],
        values["final_grade"],
        values["logo"],
        values["assignments"],
        items,
    )


def prompt_assignments() -> str:
    line = input("Assignments (semicolon-separated, or blank for multi-line): ").strip()
    if line:
        return line
    print("Enter assignments over multiple lines; end with a blank line.")
    lines = []
    while True:
        entry = input().strip()
        if not entry:
            break
        lines.append(entry)
    return " ".join(lines)


def slugify(text: str, lower: bool = True) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", text.strip())
    cleaned = cleaned.strip("-")
    if not cleaned:
        return "student"
    return cleaned.lower() if lower else cleaned


def build_latex(
    name: str,
    student_id: str,
    email: str,
    address: str,
    cell: str,
    college: str,
    class_year: str,
    course: str,
    section: str,
    sem_year: str,
    instructor: str,
    reason: str,
    percent_complete: str,
    average: str,
    deadline: str,
    final_grade: str,
    items: list[tuple[str, str]],
    logo_filename: str,
) -> str:
    if email and "@" not in email:
        email = ""

    assignment_rows = []
    if not items:
        assignment_rows.append(r"\underline{\hspace{4.5in}} & \\")
    else:
        for item, due in items:
            left = latex_escape(item) if item else r"\underline{\hspace{4.5in}}"
            right = latex_escape(due) if due else ""
            assignment_rows.append(f"{left} & {right} \\\\")

    assignments_block = "\n".join(assignment_rows)

    logo_block = ""
    if logo_filename:
        logo_block = r"\noindent\includegraphics[height=0.55in]{" + logo_filename + r"}\par\vspace{0.1in}"

    return r"""\documentclass[11pt]{article}
\usepackage[margin=0.85in]{geometry}
\usepackage{longtable}
\usepackage{array}
\usepackage{parskip}
\usepackage{graphicx}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\begin{document}
""" + logo_block + r"""
\begin{center}
{\Large \textbf{INCOMPLETE GRADE REPORT}}
\end{center}
\vspace{0.2in}
\begin{center}
\textbf{\textit{Completed forms must be returned to the school/college of course enrollment.}}
\end{center}
\vspace{0.15in}
\begin{center}
\textit{Note: Incomplete grades must be resolved within the time period allowed by the individual school or college of course
enrollment, or the maximum of one year (whichever comes first), at which time the grade will be converted to the final
grade indicated below, or `F' if no grade is indicated. In CGS and Questrom, grades must be resolved by the end of the
following semester.}
\end{center}
\vspace{0.15in}

\vspace{0.1in}
\textbf{Student Information:} \\
\begin{tabular}{@{}p{3.9in}p{2.5in}@{}}
Name: """ + field(name, "2.9in") + r""" & BU ID \#: """ + field(student_id, "1.4in") + r""" \\
Address: """ + field(address, "3.2in") + r""" & \\
Email: """ + field(email, "2.4in") + r""" & Cell Phone \#: """ + field(cell, "1.3in") + r""" \\
College: """ + field(college, "2.2in") + r""" & Class Year: """ + field(class_year, "1.0in") + r""" \\
Course: """ + field(course, "1.9in") + r""" & Section: """ + field(section, "1.1in") + r""" \\
Sem/Year: """ + field(sem_year, "1.6in") + r""" & Instructor: """ + field(instructor, "1.6in") + r""" \\
\end{tabular}


\vspace{0.1in}
\textbf{To be completed by the instructor:}

Reason for Incomplete Grade: """ + field(reason, "4.9in") + r"""

To date, the student has completed """ + inline_field(percent_complete, "0.9in") + r""" with an average of """ + inline_field(average, "0.9in") + r""" for the portion of work completed.

If the student fails to complete the missing work by """ + inline_field(deadline, "2.3in") + r""", the final grade to be recorded is """ + inline_field(final_grade, "1.0in") + r""".

Assignment(s) to be completed:

\begin{longtable}{p{4.9in} p{1.2in}}
\textbf{Requirement} & \textbf{Deadline} \\
\hline
""" + assignments_block + r"""
\end{longtable}

I have been in contact with the student regarding the `I' grade for this course.

\vspace{0.6in}
Instructor Signature: \underline{\hspace{2.6in}} \hfill Date: \underline{\hspace{1.2in}}

Student Signature: \underline{\hspace{2.6in}} \hfill Date: \underline{\hspace{1.2in}}

\end{document}
"""


def main() -> None:
    enable_tab_completion()
    p = argparse.ArgumentParser(description="Generate an incomplete grade form PDF")
    p.add_argument("--out", default="")
    p.add_argument("--name", default="")
    p.add_argument("--student-id", dest="student_id", default="")
    p.add_argument("--email", default="")
    p.add_argument("--address", default="")
    p.add_argument("--cell", default="")
    p.add_argument("--college", default="")
    p.add_argument("--class-year", dest="class_year", default="")
    p.add_argument("--course", default="")
    p.add_argument("--section", default="")
    p.add_argument("--sem-year", dest="sem_year", default="")
    p.add_argument("--instructor", default="")
    p.add_argument("--reason", default="")
    p.add_argument("--percent-complete", dest="percent_complete", default="")
    p.add_argument("--average", default="")
    p.add_argument("--deadline", default="")
    p.add_argument("--final-grade", dest="final_grade", default="")
    p.add_argument("--assignments", default="")
    p.add_argument("--deadline-all", dest="deadline_all", default="")
    p.add_argument("--fill-deadlines", action="store_true", help="Fill each assignment deadline with the same date")
    p.add_argument("--logo", default="")
    args = p.parse_args()

    name = args.name or prompt("Student name")
    student_id = args.student_id or prompt("BU ID #")
    email = args.email or prompt("Email")
    address = args.address or prompt("Address")
    cell = args.cell or prompt("Cell phone #")
    college = args.college or prompt("College of enrollment")
    class_year = args.class_year or prompt("Class year")
    course = args.course or prompt("Course")
    section = args.section or prompt("Section")
    sem_year = args.sem_year or prompt("Sem/Year")
    instructor = args.instructor or prompt("Instructor's name")
    reason = args.reason or prompt("Reason for incomplete grade")
    percent_complete = args.percent_complete or prompt("Percent complete")
    average = args.average or prompt("Average for completed work")
    default_logo_name = "boston-univ.gif" if (Path(__file__).parent / "boston-univ.gif").exists() else ""
    logo_name = args.logo or prompt("Logo filename (optional)", default_logo_name)

    deadline_all = args.deadline_all
    fill_deadlines = args.fill_deadlines
    if not deadline_all:
        if prompt_yes_no("Use one deadline for all assignments?", default=False):
            deadline_all = prompt("Deadline for all assignments (e.g., 1/26/26)")
            fill_deadlines = prompt_yes_no("Fill each assignment deadline with this date?", default=False)

    percent_complete = add_percent_if_numeric(percent_complete)
    average = add_percent_if_numeric(average)
    deadline = args.deadline or deadline_all or prompt("Overall deadline (leave blank if not used)")
    final_grade = args.final_grade or prompt("Final grade if incomplete")

    assignment_text = args.assignments or prompt_assignments()
    items = parse_assignments(assignment_text)
    if fill_deadlines and deadline_all:
        items = [(name, due or deadline_all) for name, due in items]
    items = pack_assignments(items)
    if deadline_all and not fill_deadlines and items:
        first_name, _ = items[0]
        items[0] = (first_name, "See above")

    (
        name,
        student_id,
        email,
        address,
        cell,
        college,
        class_year,
        course,
        section,
        sem_year,
        instructor,
        reason,
        percent_complete,
        average,
        deadline,
        final_grade,
        logo_name,
        assignment_text,
        items,
    ) = edit_loop(
        name,
        student_id,
        email,
        address,
        cell,
        college,
        class_year,
        course,
        section,
        sem_year,
        instructor,
        reason,
        percent_complete,
        average,
        deadline,
        final_grade,
        logo_name,
        assignment_text,
        items,
    )

    logo_path = resolve_logo_path(logo_name)

    items = parse_assignments(assignment_text)
    if fill_deadlines and deadline_all:
        items = [(name, due or deadline_all) for name, due in items]
    items = pack_assignments(items)
    if deadline_all and not fill_deadlines and items:
        first_name, _ = items[0]
        items[0] = (first_name, "See above")

    last_name = name.split()[-1] if name.split() else "student"
    student_id_slug = slugify((student_id or "id").upper(), lower=False)
    default_name = f"incomplete-{slugify(last_name)}-{student_id_slug}.pdf"
    out_path = Path(args.out) if args.out else Path(default_name)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tex_path = tmpdir_path / "form.tex"
        logo_filename = ""
        logo_source = Path(logo_path).expanduser() if logo_path else None
        if logo_source and logo_source.exists():
            if logo_source.suffix.lower() == ".gif":
                logo_filename = "logo.png"
                logo_target = tmpdir_path / logo_filename
                result = subprocess.run(
                    ["convert", str(logo_source), str(logo_target)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    raise SystemExit(result.stdout + "\n" + result.stderr)
            else:
                logo_filename = "logo" + logo_source.suffix.lower()
                shutil.copyfile(logo_source, tmpdir_path / logo_filename)

        latex = build_latex(
            name,
            student_id,
            email,
            address,
            cell,
            college,
            class_year,
            course,
            section,
            sem_year,
            instructor,
            reason,
            percent_complete,
            average,
            deadline,
            final_grade,
            items,
            logo_filename,
        )
        tex_path.write_text(latex, encoding="utf-8")

        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-output-directory",
                str(tmpdir_path),
                str(tex_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit(result.stdout + "\n" + result.stderr)

        pdf_path = tmpdir_path / "form.pdf"
        shutil.copyfile(pdf_path, out_path)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
