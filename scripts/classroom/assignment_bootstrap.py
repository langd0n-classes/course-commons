#!/usr/bin/env python3
"""
assignment_bootstrap_noopen.py

Same as assignment_bootstrap.py but **never opens a browser** — only prints URLs.
Supports -n/--dry-run with checklist and commands.
"""
import os
import re
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"

DRY_RUN = False
PLAN = []

def add_plan(step_type, desc, cmd=None, url=None):
    PLAN.append({"type": step_type, "desc": desc, "cmd": cmd, "url": url})

def say(header, detail=""):
    print(f"{BOLD}{header}{RESET}")
    if detail:
        print(detail)

def ok(msg):
    print(f"{GREEN}✔ {msg}{RESET}")

def warn(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def err(msg):
    print(f"{RED}✘ {msg}{RESET}")

def ask(prompt, default=None, validator=None):
    while True:
        if default is not None:
            resp = input(f"{BLUE}{prompt} [{default}]: {RESET}").strip()
            if resp == "":
                resp = default
        else:
            resp = input(f"{BLUE}{prompt}: {RESET}").strip()
        if validator:
            try:
                if validator(resp):
                    return resp
            except Exception as e:
                warn(str(e))
        else:
            return resp

def yesno(msg, default_yes=True):
    suffix = "[Y/n]" if default_yes else "[y/N]"
    ans = input(f"{BLUE}{msg} {suffix} {RESET}").strip().lower()
    if not ans:
        return default_yes
    return ans in ("y", "yes")

def sh(cmd, check=True, capture_output=True, text=True):
    cmd_str = " ".join(cmd)
    if DRY_RUN:
        print(f"{YELLOW}[DRY RUN]{RESET} {cmd_str}")
        add_plan("AUTO", f"Execute: {cmd_str}", cmd=cmd_str)
        class Dummy:
            returncode = 0
            stdout = ""
            stderr = ""
        return Dummy()
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=text)

def require(cmd_name, install_hint=""):
    if shutil.which(cmd_name) is None:
        err(f"Missing required command: {cmd_name}")
        if install_hint:
            print(install_hint)
        sys.exit(1)

def require_gh():
    if DRY_RUN:
        ok("Skipping gh auth check (dry run).")
        add_plan("AUTO", "Verify gh authentication", cmd="gh auth status")
        return
    require("gh", "Install: https://github.com/cli/cli")
    try:
        sh(["gh", "auth", "status"])
        ok("GitHub CLI authentication looks good.")
    except subprocess.CalledProcessError as e:
        err("GitHub CLI not authenticated.")
        print(e.stderr.strip())
        print("Run: gh auth login")
        sys.exit(1)

def sanitize_slug(s: str) -> str:
    s = s.strip().lower()
    s = s.replace(" ", "-").replace("_", "-")
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")

def repo_exists(org, repo):
    try:
        sh(["gh", "api", f"/repos/{org}/{repo}"])
        return True
    except subprocess.CalledProcessError:
        return False

def create_repo(org, name, private=True, description=""):
    vis_flag = "--private" if private else "--public"
    cmd = ["gh", "repo", "create", f"{org}/{name}", vis_flag, "--add-readme"]
    add_plan("AUTO", f"Create repo {org}/{name} ({'private' if private else 'public'})", cmd=" ".join(cmd))
    sh(cmd)
    ok(f"Repository created: {org}/{name}")

def set_repo_template(org, name, is_template=True):
    flag = "true" if is_template else "false"
    cmd = ["gh", "api", "-X", "PATCH", f"/repos/{org}/{name}", "-f", f"is_template={flag}"]
    add_plan("AUTO", f"Mark {org}/{name} as template={flag}", cmd=" ".join(cmd))
    sh(cmd)
    ok(f"Set template flag on {org}/{name}")

def clone_repo(org, name, dest_dir):
    from pathlib import Path
    dest = Path(dest_dir)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", f"git@github.com:{org}/{name}.git", str(dest)]
    add_plan("AUTO", f"Clone {org}/{name} to {dest}", cmd=" ".join(cmd))
    sh(cmd)
    ok(f"Cloned to {dest}")

def copy_student_payload(instructor_root, slug, repo_dir):
    src = Path(instructor_root) / "dist" / slug / "student"
    dst = Path(repo_dir)
    if not src.exists():
        err(f"Student payload not found at: {src}")
        sys.exit(1)
    if shutil.which("rsync"):
        cmd = ["rsync", "-av", f"{src}/", f"{dst}/"]
    else:
        cmd = ["bash", "-lc", f"cp -a '{src}/.' '{dst}/'"]
    add_plan("AUTO", f"Copy starter files from {src} into repo", cmd=" ".join(cmd))
    sh(cmd)
    ok(f"Copied starter files from {src}")

def git_commit_push(repo_dir, message):
    cmd_add = ["git", "-C", str(repo_dir), "add", "."]
    cmd_commit = ["git", "-C", str(repo_dir), "commit", "-m", message]
    cmd_push = ["git", "-C", str(repo_dir), "push", "origin", "HEAD"]
    add_plan("AUTO", f"Stage files", cmd=" ".join(cmd_add))
    sh(cmd_add, check=False)
    add_plan("AUTO", f"Commit files", cmd=" ".join(cmd_commit))
    sh(cmd_commit, check=False)
    add_plan("AUTO", f"Push to origin", cmd=" ".join(cmd_push))
    sh(cmd_push, check=False)
    ok("Pushed starter files")

def classroom_step(org, repo_name):
    url = "https://classroom.github.com/"
    add_plan("MANUAL", f"Create a new Classroom assignment using template repo {org}/{repo_name}.", url=url)
    say("Manual step: Create the Classroom assignment",
        f"Open GitHub Classroom and create a new assignment.\n"
        f"When prompted to choose a template repository, select: {org}/{repo_name}\n"
        f"URL: {url}")

def gradescope_reminder(slug, name):
    add_plan("MANUAL", "Create matching Gradescope assignment and upload autograder.zip", url="https://www.gradescope.com/")
    say("Reminder: Gradescope",
        "Create the matching Gradescope assignment and upload your autograder zip.\n"
        f"Suggested title: {name} ({slug})\n"
        f"URL: https://www.gradescope.com/")

def print_plan():
    if not PLAN:
        return
    print()
    say("Checklist / Plan")
    for i, step in enumerate(PLAN, 1):
        tag = "🧭 MANUAL" if step["type"] == "MANUAL" else "⚙️  AUTO"
        print(f"{i:2d}. {tag} — {step['desc']}")
        if step.get("url"):
            print(f"    ↳ URL: {step['url']}")
        if step.get("cmd"):
            print(f"    ↳ CMD: {step['cmd']}")
    print()

def main():
    global DRY_RUN
    if "-n" in sys.argv or "--dry-run" in sys.argv:
        DRY_RUN = True
        warn("Running in DRY RUN mode (no changes will be made).")
        sys.argv = [a for a in sys.argv if a not in ("-n","--dry-run")]

    say("Assignment Bootstrapper (No-Open URLs)")

    require_gh()
    require("git", "Install git via your package manager.")

    org = ask("GitHub organization slug (e.g., bu-ds100-f25)")
    assignment_name = ask("Assignment display name (e.g., 'Exploration 01 – Morning Routine')")
    assignment_slug = sanitize_slug(ask("Assignment slug (filesystem/repo-safe, e.g., 'exploration-01')"))
    default_instructor = os.getcwd()
    instructor_root = ask("Path to your instructor repo root (containing 'dist/<slug>/student')", default=default_instructor,
                          validator=lambda p: True)
    base_dir = ask("Local directory to place cloned assignments (default: ./gh-assignments)", default="gh-assignments")
    private_repo = yesno("Make the new repository PRIVATE?", default_yes=True)

    name_slug = sanitize_slug(assignment_name)
    repo_name = f"{assignment_slug}--{name_slug}" if name_slug != assignment_slug else assignment_slug
    warn(f"Planned repository name: {org}/{repo_name}")

    if repo_exists(org, repo_name):
        warn("Repo already exists; will reuse.")
    else:
        create_repo(org, repo_name, private=private_repo, description=f"Starter for {assignment_name}")

    set_repo_template(org, repo_name, is_template=True)

    target_dir = Path(base_dir).expanduser().resolve() / assignment_slug
    if target_dir.exists() and any(target_dir.iterdir()):
        warn(f"Target directory already exists and is non-empty: {target_dir}")
    else:
        clone_repo(org, repo_name, target_dir)

    copy_student_payload(instructor_root, assignment_slug, target_dir)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    git_commit_push(target_dir, f"Add starter files for {assignment_name} ({assignment_slug}) @ {ts}")

    classroom_step(org, repo_name)
    gradescope_reminder(assignment_slug, assignment_name)

    if DRY_RUN:
        print_plan()

    ok("Assignment bootstrap flow complete.")
    print("\nNext: In Classroom, when asked for a template repository, pick "
          f"{org}/{repo_name}. Then set deadlines, visibility, and autograder as needed.")
    print("After creating the Gradescope assignment, link it in your course tracker.")

if __name__ == "__main__":
    main()
