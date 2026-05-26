#!/usr/bin/env python3
"""
grade_anon.py  –  Anonymize / deanonymize Gradescope and Blackboard grade CSVs.

PII stripped on anonymize
  Gradescope : First Name, Last Name, SID, Email
  Blackboard : Last Name, First Name, Username, Student ID

All other columns (scores, Last Access, Availability, …) are kept intact.

The mapping CSV stores all PII so any student can be looked up by anon_id.
Its first two columns (anon_id, username) are compatible with the existing
anonymize.py / deanonymize_and_score.py pipeline.

Student ID / SID is the primary key used to link Gradescope ↔ Blackboard
records.  Email is stored for reference only and is NOT used for matching.

Usage
─────
  python grade_anon.py anonymize   --input grades.csv --output anon.csv     --mapping mapping.csv
  python grade_anon.py deanonymize --input anon.csv   --output restored.csv --mapping mapping.csv
"""

import argparse
import csv
import sys
from pathlib import Path
from uuid import uuid4

# ─── constants ───────────────────────────────────────────────────────────────

ANON_COL = "anon_id"

# PII column lists in the order they appear at the start of each file.
# This order is also used when restoring them on deanonymize.
GS_PII = ["First Name", "Last Name", "SID", "Email"]
BB_PII = ["Last Name", "First Name", "Username", "Student ID"]

MAPPING_FIELDS = ["anon_id", "username", "first_name", "last_name", "student_id", "email"]


# ─── utilities ───────────────────────────────────────────────────────────────

def _new_id(taken: set) -> str:
    """Return a unique 10-hex-char anonymous ID not already in *taken*."""
    while True:
        cid = uuid4().hex[:10]
        if cid not in taken:
            return cid


def _confirm_overwrite(path: Path) -> None:
    """Prompt before overwriting an existing output file; exits if declined."""
    if path.exists():
        ans = input(f"  '{path}' already exists — overwrite? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            sys.exit("Aborted.")


def _detect_deanon_format(score_cols: list) -> str:
    """Guess the original export format from remaining column names, then confirm."""
    joined = " ".join(score_cols)
    guess = "blackboard" if ("Last Access" in joined or "[Total Pts:" in joined) else "gradescope"
    ans = input(f"  Detected format: {guess} — correct? [Y/n] ").strip().lower()
    if ans in ("", "y", "yes"):
        return guess
    while True:
        fmt = input("  Enter format (gradescope / blackboard): ").strip().lower()
        if fmt in ("gradescope", "gs"):
            return "gradescope"
        if fmt in ("blackboard", "bb"):
            return "blackboard"
        print("  Please enter 'gradescope' (or 'gs') / 'blackboard' (or 'bb').")


def detect_format(headers: list) -> str:
    """Return ``'gradescope'`` or ``'blackboard'``, or raise ValueError."""
    h = set(headers)
    if {"SID", "Email", "First Name"} <= h:
        return "gradescope"
    if {"Username", "Student ID"} <= h:
        return "blackboard"
    raise ValueError(
        f"Unrecognised format — cannot find expected PII columns.\n"
        f"First 8 headers seen: {headers[:8]}"
    )


# ─── mapping I/O ─────────────────────────────────────────────────────────────

def load_mapping(path: Path) -> tuple:
    """
    Load mapping CSV.

    Returns
    -------
    by_sid : dict  student_id → row_dict
    by_un  : dict  username   → row_dict
        (by_un is used as a fallback for older mapping files that
         pre-date this script and therefore have no student_id column)
    """
    by_sid, by_un = {}, {}
    if not path.exists():
        return by_sid, by_un
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            row = {k: (v or "").strip() for k, v in row.items()}
            sid = row.get("student_id")
            un  = row.get("username")
            if sid:
                by_sid[sid] = row
            elif un:
                # No student_id yet — store under synthetic key so save_mapping
                # doesn't silently drop entries from old mapping files.
                by_sid[f"__orphan__{un}"] = row
            if un:
                by_un[un] = row
    return by_sid, by_un


def save_mapping(by_sid: dict, path: Path) -> None:
    """Write mapping sorted alphabetically by last name."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MAPPING_FIELDS, extrasaction="ignore")
        w.writeheader()
        rows = sorted(by_sid.values(), key=lambda r: r.get("last_name", "").lower())
        for row in rows:
            w.writerow({field: row.get(field, "") for field in MAPPING_FIELDS})


# ─── anonymize core ──────────────────────────────────────────────────────────

def _anonymize(
    rows: list,
    headers: list,
    pii_cols: list,
    extract,            # callable(row) -> (sid, username, first, last, email)
    mapping_path: Path,
    authoritative_username: bool,
) -> tuple:
    """
    Strip pii_cols from every row and prepend an anon_id column.

    Matching is done by student_id (SID) as the primary key.
    Falls back to username match for backward-compat with old mapping files.

    authoritative_username: if True (Blackboard), always overwrite the stored
    username with the value from this file.  If False (Gradescope), the
    username is derived from the email prefix and only fills an empty slot.

    Returns (out_rows, out_headers).
    """
    by_sid, by_un = load_mapping(mapping_path)
    taken = {e["anon_id"] for e in by_sid.values() if e.get("anon_id")}

    score_cols  = [h for h in headers if h not in set(pii_cols)]
    out_headers = [ANON_COL] + score_cols
    out_rows    = []

    for row in rows:
        sid, username, first, last, email = extract(row)

        if not sid:
            label = f"{first} {last}".strip() or "(unknown)"
            print(f"  SKIP (no student ID): {label}", file=sys.stderr)
            continue

        # ── find or create mapping entry ─────────────────────────────────
        if sid in by_sid:
            entry = by_sid[sid]

        elif username and username in by_un:
            # Backward-compat: old mapping had no student_id column — adopt entry
            entry               = by_un[username]
            entry["student_id"] = sid
            by_sid[sid]         = entry
            by_sid.pop(f"__orphan__{username}", None)  # promote; drop placeholder

        else:
            anon_id = _new_id(taken)
            taken.add(anon_id)
            entry = {
                "anon_id":    anon_id,
                "username":   username,
                "first_name": first,
                "last_name":  last,
                "student_id": sid,
                "email":      email,
            }
            by_sid[sid] = entry

        # ── update PII fields ────────────────────────────────────────────
        # Blackboard is the authoritative source of username; always write it.
        # Gradescope derives username from email prefix — only fill if missing.
        if authoritative_username and username:
            entry["username"] = username
        elif username and not entry.get("username"):
            entry["username"] = username

        if email  and not entry.get("email"):      entry["email"]      = email
        if first  and not entry.get("first_name"): entry["first_name"] = first
        if last   and not entry.get("last_name"):  entry["last_name"]  = last

        # ── build anonymized row ─────────────────────────────────────────
        out_row = {ANON_COL: entry["anon_id"]}
        for col in score_cols:
            out_row[col] = row.get(col, "")
        out_rows.append(out_row)

    save_mapping(by_sid, mapping_path)
    return out_rows, out_headers


# ─── format-specific anonymize wrappers ──────────────────────────────────────

def anonymize_gradescope(src: Path, dst: Path, mapping: Path) -> None:
    with open(src, "r", encoding="utf-8-sig", newline="") as f:
        reader  = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows    = list(reader)

    def extract(row):
        sid      = row.get("SID",        "").strip()
        email    = row.get("Email",      "").strip()
        first    = row.get("First Name", "").strip()
        last     = row.get("Last Name",  "").strip()
        # Derive username from email prefix as best-effort fallback.
        # Will be overwritten by the authoritative Blackboard username if
        # the Blackboard gradebook is also anonymized with the same mapping.
        username = email.split("@")[0] if email else ""
        return sid, username, first, last, email

    out_rows, out_headers = _anonymize(
        rows, headers, GS_PII, extract, mapping,
        authoritative_username=False,
    )

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_headers)
        w.writeheader()
        w.writerows(out_rows)

    print(f"  Gradescope : {len(out_rows)} students → {dst}")


def anonymize_blackboard(src: Path, dst: Path, mapping: Path) -> None:
    with open(src, "r", encoding="utf-8-sig", newline="") as f:
        reader  = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows    = list(reader)

    def extract(row):
        sid      = row.get("Student ID", "").strip()
        username = row.get("Username",   "").strip()
        first    = row.get("First Name", "").strip()
        last     = row.get("Last Name",  "").strip()
        return sid, username, first, last, ""  # Blackboard has no email column

    out_rows, out_headers = _anonymize(
        rows, headers, BB_PII, extract, mapping,
        authoritative_username=True,  # Blackboard username is the ground truth
    )

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_headers)
        w.writeheader()
        w.writerows(out_rows)

    print(f"  Blackboard : {len(out_rows)} students → {dst}")


# ─── deanonymize ─────────────────────────────────────────────────────────────

def deanonymize(src: Path, dst: Path, mapping: Path) -> None:
    if not mapping.exists():
        sys.exit(f"ERROR: mapping file not found: {mapping}")

    # Index mapping by anon_id for O(1) lookup
    by_anon: dict = {}
    with open(mapping, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            row = {k: (v or "").strip() for k, v in row.items()}
            if row.get("anon_id"):
                by_anon[row["anon_id"]] = row

    with open(src, "r", encoding="utf-8-sig", newline="") as f:
        reader  = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows    = list(reader)

    if ANON_COL not in headers:
        sys.exit(
            f"ERROR: column '{ANON_COL}' not found in {src}.\n"
            "       Are you sure this is an anonymized file?"
        )

    score_cols = [h for h in headers if h != ANON_COL]

    # ── detect original format and confirm with user ──────────────────────
    fmt = _detect_deanon_format(score_cols)
    if fmt == "blackboard":
        pii_cols = BB_PII
        pii_key  = {
            "Last Name":  "last_name",
            "First Name": "first_name",
            "Username":   "username",
            "Student ID": "student_id",
        }
        out_enc  = "utf-8-sig"
    else:
        pii_cols = GS_PII
        pii_key  = {
            "First Name": "first_name",
            "Last Name":  "last_name",
            "SID":        "student_id",
            "Email":      "email",
        }
        out_enc  = "utf-8"

    out_headers = pii_cols + score_cols
    out_rows    = []
    missing     = 0

    for row in rows:
        aid   = row.get(ANON_COL, "").strip()
        entry = by_anon.get(aid)

        if entry is None:
            print(f"  WARNING: no mapping entry for anon_id='{aid}'", file=sys.stderr)
            missing += 1
            out_row = {col: "" for col in pii_cols}
        else:
            out_row = {col: entry.get(pii_key[col], "") for col in pii_cols}

        for col in score_cols:
            out_row[col] = row.get(col, "")
        out_rows.append(out_row)

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding=out_enc, newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_headers)
        w.writeheader()
        w.writerows(out_rows)

    print(f"  {fmt.title()} : {len(out_rows)} rows restored → {dst}")
    if missing:
        print(f"  WARNING: {missing} row(s) had no mapping entry", file=sys.stderr)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    for mode in ("anonymize", "deanonymize"):
        p = sub.add_parser(mode)
        p.add_argument("--input",   required=True, metavar="FILE", help="Input CSV")
        p.add_argument("--output",  required=True, metavar="FILE", help="Output CSV")
        p.add_argument(
            "--mapping", required=True, metavar="FILE",
            help="Mapping CSV (created/updated by anonymize; read-only for deanonymize)",
        )

    args    = parser.parse_args()
    src     = Path(args.input)
    dst     = Path(args.output)
    mapping = Path(args.mapping)

    if not src.exists():
        sys.exit(f"ERROR: input file not found: {src}")

    if args.mode == "anonymize":
        # Peek at the header row to detect format before loading the whole file
        with open(src, "r", encoding="utf-8-sig", newline="") as f:
            first_row = next(csv.reader(f))
        fmt = detect_format(first_row)

        print(f"Detected : {fmt}")
        print(f"Input    : {src}")
        print(f"Output   : {dst}")
        print(f"Mapping  : {mapping}")
        _confirm_overwrite(dst)

        if fmt == "gradescope":
            anonymize_gradescope(src, dst, mapping)
        else:
            anonymize_blackboard(src, dst, mapping)

        print(f"  WARNING: '{mapping}' contains all student PII — keep it out of shared folders.")

    else:  # deanonymize
        print(f"Input    : {src}")
        print(f"Output   : {dst}")
        print(f"Mapping  : {mapping}")
        _confirm_overwrite(dst)
        deanonymize(src, dst, mapping)

    print("Done.")


if __name__ == "__main__":
    main()