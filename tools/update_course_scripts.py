#!/usr/bin/env python3
import argparse, os, shutil, sys

def copy_tree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target_root = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(target_root, exist_ok=True)
        for d in dirs:
            os.makedirs(os.path.join(target_root, d), exist_ok=True)
        for f in files:
            s = os.path.join(root, f)
            t = os.path.join(target_root, f)
            shutil.copy2(s, t)
            # preserve executable bit
            st = os.stat(s)
            os.chmod(t, st.st_mode)

def main():
    p = argparse.ArgumentParser(description="Sync course-commons/scripts into a course repo.")
    p.add_argument("--course", required=True, help="Path to the course repo root (contains course-info/)")
    p.add_argument("--src", default=None, help="Override source scripts path (defaults to ../scripts relative to this tool)")
    p.add_argument("--ensure-instructor", action="store_true", help="Create .instructor in course root if missing")
    p.add_argument("--dry-run", action="store_true", help="Show plan without copying")
    args = p.parse_args()

    course_root = os.path.abspath(args.course)
    if not os.path.isdir(course_root):
        sys.exit(f"Course path not found: {course_root}")

    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, ".."))
    src_scripts = args.src or os.path.join(repo_root, "scripts")
    if not os.path.isdir(src_scripts):
        sys.exit(f"Source scripts path not found: {src_scripts}")

    dst_scripts = os.path.join(course_root, "course-info", "scripts")

    print("=== plan ===")
    print(f"source: {src_scripts}")
    print(f"target: {dst_scripts}")
    if args.ensure_instructor and not os.path.exists(os.path.join(course_root, ".instructor")):
        print("ensure: will create .instructor in course root")

    if args.dry_run:
        print("(dry-run) no changes made")
        return

    os.makedirs(os.path.join(course_root, "course-info"), exist_ok=True)
    copy_tree(src_scripts, dst_scripts)

    if args.ensure_instructor:
        inst = os.path.join(course_root, ".instructor")
        if not os.path.exists(inst):
            with open(inst, "w", encoding="utf-8") as f:
                f.write("")
            print("Created .instructor")

    print("Done. Remember to git add/commit in the course repo.")

if __name__ == "__main__":
    main()
