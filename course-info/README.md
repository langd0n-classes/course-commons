# course-info

Data under this directory drive lecture-schedule generation for CDS courses.

## Key files

- `academic-calendar-2025-2027.md`: human- and machine-readable reference for holidays, recesses, and substitute days.
- `ay-YYYY-YY.json`: term-level calendars (start/end dates, `noClass` ranges, `substituteDays`). Each academic year (2025-26, 2026-27) has a dedicated JSON so the generator can apply the same rules across terms.
- `courses.yaml`: per-course metadata (slugs, lecture days, and term ranges). Use this file to introduce new courses or terms.
- `lecture-schedules/*.yaml`: generated outputs mapping each lecture number to its calendar date per course+term. These are the artifacts consumed by downstream tools.

## Regenerate lecture schedules

1. Ensure dependencies are installed (`pip install -r scripts/requirements.txt`).
2. Run the generator from the repo root:
   ```bash
   python scripts/gen_lecture_schedule.py
   ```
   Use `--slug` and/or `--term` to target specific outputs when needed (e.g., `python scripts/gen_lecture_schedule.py --slug ds551 --term spring_2026`).
3. Inspect `course-info/lecture-schedules/` for the YAML files, then commit them.

## Adding a new academic year

1. When a new calendar cycle starts, extend `academic-calendar-2025-2027.md` (or provide a similar human/machine reference) and author a matching `course-info/ay-YYYY-YY.json` that keeps the same schema (`term`, `start`, `end`, `noClass`, `substituteDays`).
2. Update `course-info/courses.yaml` if new terms require schedules.
3. Re-run the generator to refresh the files under `course-info/lecture-schedules/`.
