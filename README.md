# course-commons

Lightweight shared assets for BU CDS courses (scripts and optional devcontainer). Keep it simple:

- **scripts/**: reusable tools you copy into a course repo (no submodules).
- **devcontainer/**: optional environment(s) you can copy when helpful.
- **tools/**: helpers to sync scripts into a course repo and to set up a root folder.

## Quick start

1. Clone this repo next to a course repo (side-by-side layout):
   ```bash
   # tree (example)
   /projects/
     course-commons/
     ds-100/
   ```

2. Sync shared scripts into a course (dry-run first):
   ```bash
   python tools/update_course_scripts.py --course ../ds-100 --dry-run
   python tools/update_course_scripts.py --course ../ds-100
   ```

   By default, this copies `scripts/` from *this* repo into
   `<course>/course-info/scripts/` (creating it if missing).

3. Add/commit in the course repo:
   ```bash
   cd ../ds-100
   git add course-info/scripts
   git commit -m "Sync shared scripts from course-commons"
   ```

4. (Optional) Make a root folder with side-by-side clones:
   ```bash
   bash tools/new_course_root.sh  # prompts for info
   ```

## Versioning recommendation

- Tag this repo when scripts are stable, e.g., `v0.1.0`.
- In course commit messages, note which tag you synced from.
- No submodules. No subtrees unless you really want them.

## Notes

- Scripts that should **not** run on instructor repos should check for a `.instructor` file in the repo root and refuse to run.
- If you forget to create `.instructor`, the sync tool can add it for you (see `--ensure-instructor`).

— Generated skeleton on 2025-09-24.
