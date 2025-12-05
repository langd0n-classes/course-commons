#!/usr/bin/env python3
"""
Enhanced Assignment Bootstrapper for GitHub Classroom

Improvements over original:
- Rich context and examples in prompts
- Tab completion for all inputs
- Auto-detection from current directory
- Config file for remembering settings
- GitHub Classroom API integration
- Works from anywhere (finds course root)
"""
import os
import re
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import PathCompleter, WordCompleter
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False
    print("⚠ Warning: prompt_toolkit not installed. Tab completion disabled.")
    print("  Install with: pip install prompt_toolkit")

# ANSI colors
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"

DRY_RUN = False
PLAN = []

def add_plan(step_type, desc, cmd=None, url=None):
    PLAN.append({"type": step_type, "desc": desc, "cmd": cmd, "url": url})

def say(header, detail=""):
    print(f"\n{BOLD}{CYAN}═══ {header} ═══{RESET}")
    if detail:
        print(f"{DIM}{detail}{RESET}")

def ok(msg):
    print(f"{GREEN}✔ {msg}{RESET}")

def warn(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def err(msg):
    print(f"{RED}✘ {msg}{RESET}")

def info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")

def ask_basic(prompt_text, default=None):
    """Fallback for when prompt_toolkit isn't available"""
    if default is not None:
        resp = input(f"{BLUE}{prompt_text} [{default}]: {RESET}").strip()
        return resp if resp else default
    return input(f"{BLUE}{prompt_text}: {RESET}").strip()

def ask(prompt_text, default=None, completer=None, context=None, examples=None):
    """Enhanced ask with context, examples, and tab completion"""
    if context:
        print(f"{DIM}{context}{RESET}")
    if examples:
        print(f"{DIM}Examples: {', '.join(examples)}{RESET}")

    if HAS_PROMPT_TOOLKIT and completer:
        try:
            result = pt_prompt(
                f"{prompt_text}: ",
                completer=completer,
                default=default or ""
            )
            return result.strip()
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(0)
    else:
        return ask_basic(prompt_text, default)

def yesno(msg, default_yes=True):
    suffix = "[Y/n]" if default_yes else "[y/N]"
    ans = input(f"{BLUE}{msg} {suffix} {RESET}").strip().lower()
    if not ans:
        return default_yes
    return ans in ("y", "yes")

def sh(cmd, check=True, capture_output=True, text=True):
    cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
    if DRY_RUN:
        print(f"{YELLOW}[DRY RUN]{RESET} {cmd_str}")
        add_plan("AUTO", f"Execute: {cmd_str}", cmd=cmd_str)
        class Dummy:
            returncode = 0
            stdout = ""
            stderr = ""
        return Dummy()
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=text, shell=isinstance(cmd, str))

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
        ok("GitHub CLI authentication verified.")
    except subprocess.CalledProcessError:
        err("GitHub CLI not authenticated.")
        print("Run: gh auth login")
        sys.exit(1)

def sanitize_slug(s: str) -> str:
    s = s.strip().lower()
    s = s.replace(" ", "-").replace("_", "-")
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")

def get_relative_or_absolute(path: Path, relative_to: Path) -> str:
    """Get relative path if possible, otherwise absolute"""
    try:
        return str(path.relative_to(relative_to))
    except ValueError:
        return str(path)

def find_course_root() -> Optional[Path]:
    """Find ds100-private root by looking for marker files"""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / '.classroom_config.json').exists():
            return parent
        if (parent / 'course-info').exists():
            return parent
    return None

def load_config(course_root: Path) -> Dict[str, Any]:
    """Load configuration from .classroom_config.json"""
    config_file = course_root / '.classroom_config.json'
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except Exception as e:
            warn(f"Could not load config: {e}")
    return {}

def save_config(course_root: Path, config: Dict[str, Any]):
    """Save configuration to .classroom_config.json"""
    config_file = course_root / '.classroom_config.json'
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        # Show path relative to course_root, or absolute if that fails
        try:
            display_path = config_file.relative_to(course_root)
        except ValueError:
            display_path = config_file
        ok(f"Config saved to {display_path}")
    except Exception as e:
        err(f"Could not save config: {e}")
        import traceback
        traceback.print_exc()

def fetch_classrooms() -> List[Dict[str, Any]]:
    """Fetch classrooms from GitHub API with full details"""
    try:
        result = sh(["gh", "api", "/classrooms"], check=True)
        classroom_list = json.loads(result.stdout)

        # Fetch full details for each classroom (includes organization)
        full_classrooms = []
        for c in classroom_list:
            try:
                detail_result = sh(["gh", "api", f"/classrooms/{c['id']}"], check=True)
                full_classrooms.append(json.loads(detail_result.stdout))
            except Exception:
                # If we can't fetch details, use what we have
                full_classrooms.append(c)

        # Sort by ID descending (newer classrooms first)
        full_classrooms.sort(key=lambda x: x['id'], reverse=True)
        return full_classrooms
    except Exception as e:
        warn(f"Could not fetch classrooms: {e}")
        return []

def fetch_assignments(classroom_id: int) -> List[Dict[str, Any]]:
    """Fetch assignments for a classroom"""
    try:
        result = sh(["gh", "api", f"/classrooms/{classroom_id}/assignments"], check=True)
        assignments = json.loads(result.stdout)
        return assignments
    except Exception as e:
        warn(f"Could not fetch assignments: {e}")
        return []

def detect_assignment_from_cwd() -> Optional[tuple]:
    """Try to detect assignment slug from current directory"""
    cwd = Path.cwd()
    parts = cwd.parts

    # Check if we're in a dist/ subdirectory
    if 'dist' in parts:
        dist_idx = parts.index('dist')
        if dist_idx + 1 < len(parts):
            slug = parts[dist_idx + 1]
            return slug, f"Detected from dist/{slug}"

    # Check if we're in gh-assignments-repos
    if 'gh-assignments-repos' in parts:
        repo_idx = parts.index('gh-assignments-repos')
        if repo_idx + 1 < len(parts):
            slug = parts[repo_idx + 1]
            return slug, f"Detected from gh-assignments-repos/{slug}"

    return None

def find_dist_folders(course_root: Path) -> List[str]:
    """Find all dist/ subfolders in course root, sorted by modification time (most recent first)"""
    dist_dir = course_root / "dist"
    if not dist_dir.exists():
        return []

    try:
        # Get folders with student/ subdirectory and their modification times
        folders_with_time = [
            (d.name, d.stat().st_mtime)
            for d in dist_dir.iterdir()
            if d.is_dir() and (d / "student").exists()
        ]
        # Sort by modification time descending (most recent first)
        folders_with_time.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in folders_with_time]
    except Exception:
        return []

def match_classroom_to_path(classroom_name: str, cwd: Path) -> bool:
    """Check if classroom name matches current working directory"""
    cwd_str = str(cwd).lower()
    name_parts = re.split(r'[-_\s]+', classroom_name.lower())

    # Look for key identifiers like "ds100", "2025", "fall"
    key_parts = [p for p in name_parts if len(p) > 2 and p.isalnum()]
    matches = sum(1 for part in key_parts if part in cwd_str)

    return matches >= 2  # Match if at least 2 key parts found

def repo_exists(org, repo):
    try:
        sh(["gh", "api", f"/repos/{org}/{repo}"])
        return True
    except subprocess.CalledProcessError:
        return False

def create_repo(org, name, private=True, description=""):
    vis_flag = "--private" if private else "--public"
    cmd = ["gh", "repo", "create", f"{org}/{name}", vis_flag, "--add-readme"]
    if description:
        cmd.extend(["-d", description])
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
        print(f"Expected path: {src.absolute()}")
        sys.exit(1)

    if shutil.which("rsync"):
        cmd = ["rsync", "-av", "--exclude=.git", f"{src}/", f"{dst}/"]
    else:
        cmd = f"cp -a '{src}/.' '{dst}/'"

    add_plan("AUTO", f"Copy starter files from {src} into repo", cmd=cmd if isinstance(cmd, str) else " ".join(cmd))
    sh(cmd)
    ok(f"Copied starter files from {src}")

def git_commit_push(repo_dir, message):
    cmd_add = ["git", "-C", str(repo_dir), "add", "."]
    cmd_commit = ["git", "-C", str(repo_dir), "commit", "-m", message]
    cmd_push = ["git", "-C", str(repo_dir), "push", "origin", "HEAD"]

    add_plan("AUTO", "Stage files", cmd=" ".join(cmd_add))
    sh(cmd_add, check=False)
    add_plan("AUTO", "Commit files", cmd=" ".join(cmd_commit))
    sh(cmd_commit, check=False)
    add_plan("AUTO", "Push to origin", cmd=" ".join(cmd_push))
    sh(cmd_push, check=False)
    ok("Pushed starter files")

def print_classroom_instructions(classroom_url, org, repo_name, assignment_name):
    say("MANUAL STEP: Create GitHub Classroom Assignment")
    print(f"""
{BOLD}GitHub Classroom does not have a public API for creating assignments.{RESET}
You'll need to complete this step manually in your browser.

{BOLD}Instructions:{RESET}
  1. Open: {CYAN}{classroom_url}{RESET}

  2. Click "{BOLD}New assignment{RESET}" or "{BOLD}Create an assignment{RESET}"

  3. Fill in the form:
     • Title: {BOLD}{assignment_name}{RESET}
       (This is what students see - can be different from slug)

     • Slug: {BOLD}{repo_name}{RESET}
       (Or let GitHub auto-generate from title)

     • Template repository: {BOLD}{org}/{repo_name}{RESET}
       {DIM}⚠ Make sure you select YOUR template repo!{RESET}

     • Deadline: {DIM}(set as needed){RESET}

     • Recommended settings:
       - Use GitHub Codespaces: {GREEN}Yes{RESET} (recommended)
       - Enable feedback pull requests: {DIM}Optional{RESET}

  4. Click "{BOLD}Create assignment{RESET}"

  5. Copy the invitation link for your records

{BOLD}URL to open:{RESET} {CYAN}{classroom_url}{RESET}
    """)
    add_plan("MANUAL", f"Create Classroom assignment using template {org}/{repo_name}", url=classroom_url)

def print_gradescope_reminder(slug, name):
    say("REMINDER: Gradescope Setup")
    print(f"""
Don't forget to create the Gradescope assignment!

{BOLD}Steps:{RESET}
  1. Go to: {CYAN}https://www.gradescope.com/{RESET}

  2. Create new assignment:
     • Title: {BOLD}{name} ({slug}){RESET}
     • Type: Programming Assignment

  3. Upload autograder:
     • Find: {BOLD}dist/{slug}/autograder/*-autograder_*.zip{RESET}
     • Upload to Gradescope

  4. Configure:
     • Set due date (match GitHub Classroom)
     • Enable manual grading if needed
     • Publish assignment

  5. Link in course tracker/spreadsheet
    """)
    add_plan("MANUAL", f"Create Gradescope assignment and upload autograder.zip", url="https://www.gradescope.com/")

def print_plan():
    if not PLAN:
        return
    print()
    say("Action Plan Summary")
    for i, step in enumerate(PLAN, 1):
        tag = "🧭 MANUAL" if step["type"] == "MANUAL" else "⚙️  AUTO"
        print(f"{i:2d}. {tag} — {step['desc']}")
        if step.get("url"):
            print(f"    ↳ URL: {CYAN}{step['url']}{RESET}")
        if step.get("cmd"):
            print(f"    ↳ CMD: {DIM}{step['cmd']}{RESET}")
    print()

def main():
    global DRY_RUN

    # Parse flags
    if "-n" in sys.argv or "--dry-run" in sys.argv:
        DRY_RUN = True
        warn("Running in DRY RUN mode (no changes will be made).")
        sys.argv = [a for a in sys.argv if a not in ("-n", "--dry-run")]

    say("Enhanced GitHub Classroom Assignment Bootstrapper")

    # Check requirements
    require_gh()
    require("git", "Install git via your package manager.")

    # Find course root
    say("Finding course root")
    course_root = find_course_root()
    if course_root:
        ok(f"Found course root: {course_root}")
    else:
        warn("Could not auto-detect course root (looking for course-info/ or .classroom_config.json)")
        course_root = Path(ask(
            "Path to ds100-private root",
            default=str(Path.cwd()),
            completer=PathCompleter() if HAS_PROMPT_TOOLKIT else None,
            context="This is the directory containing course-info/, dist/, etc."
        )).expanduser().resolve()

    # Load config
    config = load_config(course_root)

    # Fetch classrooms from API
    say("Fetching GitHub Classrooms")
    classrooms = fetch_classrooms()

    if classrooms:
        ok(f"Found {len(classrooms)} classroom(s)")
        classroom_map = {c['name']: c for c in classrooms}
        classroom_names = list(classroom_map.keys())
        cwd = Path.cwd()

        # Show available classrooms with bold matching
        print(f"\n{BOLD}Available classrooms:{RESET}")
        for i, name in enumerate(classroom_names, 1):
            is_match = match_classroom_to_path(name, cwd)
            is_default = name == config.get('last_classroom_name')
            prefix = "→" if is_default else " "
            display_name = f"{BOLD}{name}{RESET}" if is_match else name
            print(f"  {prefix} {i}. {display_name}")

        # Find first matching classroom for default
        matching_classroom = None
        for name in classroom_names:
            if match_classroom_to_path(name, cwd):
                matching_classroom = name
                break

        default_classroom = config.get('last_classroom_name') or classroom_names[0]  # Just use first classroom, not matching

        classroom_choice = ask(
            "\nSelect classroom (number or name)",
            default=default_classroom,
            completer=WordCompleter(classroom_names, ignore_case=True) if HAS_PROMPT_TOOLKIT else None,
            context="Type a number (e.g., '14'), name, or use tab completion"
        )

        # Handle numeric input
        if classroom_choice.isdigit():
            choice_idx = int(classroom_choice) - 1
            if 0 <= choice_idx < len(classroom_names):
                classroom_name = classroom_names[choice_idx]
            else:
                err(f"Invalid number: {classroom_choice}. Must be 1-{len(classroom_names)}")
                sys.exit(1)
        else:
            classroom_name = classroom_choice

        if classroom_name not in classroom_map:
            err(f"Invalid classroom: {classroom_name}")
            sys.exit(1)

        classroom = classroom_map[classroom_name]
        # Safely get organization (might not be present in all responses)
        org = classroom.get('organization', {}).get('login')
        if not org:
            err("Could not determine organization from classroom. Please enter manually.")
            org = ask("GitHub organization slug", context="Example: BU-CDS-DS100-2025-Fall")
            if not org:
                sys.exit(1)
        classroom_id = classroom['id']
        classroom_url = classroom['url']

        ok(f"Selected: {classroom_name}")
        info(f"Organization: {org}")

        # Fetch existing assignments for context
        assignments = fetch_assignments(classroom_id)
        if assignments:
            existing_slugs = [a['slug'] for a in assignments[:10]]
            info(f"Recent assignment slugs: {', '.join(existing_slugs)}")
    else:
        warn("Could not fetch classrooms via API. Manual entry required.")
        org = ask(
            "GitHub organization slug",
            default=config.get('last_org'),
            context="The GitHub organization for this course",
            examples=["bu-ds100-f25", "BU-CDS-DS100-2025-Fall"]
        )
        classroom_url = "https://classroom.github.com/"
        classroom_id = None
        existing_slugs = []

    # Detect assignment from current directory
    say("Assignment Details")
    detected = detect_assignment_from_cwd()
    if detected:
        slug, reason = detected
        info(reason)
        use_detected = yesno(f"Use detected slug '{slug}'?", default_yes=True)
        if use_detected:
            assignment_slug = slug
        else:
            assignment_slug = None
    else:
        assignment_slug = None

    # Ask for assignment details
    if not assignment_slug:
        # Find available dist folders for suggestions
        dist_folders = find_dist_folders(course_root) if course_root else []
        if dist_folders:
            info(f"Available in dist/: {', '.join(dist_folders[:10])}")

        # Combine existing slugs from API and dist folders
        all_suggestions = list(set(existing_slugs + dist_folders)) if existing_slugs else dist_folders

        assignment_slug = sanitize_slug(ask(
            "Assignment slug (filesystem/repo-safe)",
            completer=WordCompleter(all_suggestions, ignore_case=True) if HAS_PROMPT_TOOLKIT and all_suggestions else None,
            context="Used for repo name and file paths. Must be lowercase, no spaces.",
            examples=dist_folders[:3] if dist_folders else ["lec25", "gai-e01", "a11", "m03d"]
        ))

    assignment_name = ask(
        "Assignment display name (for students)",
        default=assignment_slug.replace("-", " ").title(),
        context="This is what students see in GitHub Classroom. Can have spaces, capitals, etc.",
        examples=["Lecture 25", "GAI Exploration 01", "Assessment 11"]
    )

    # Instructor root path
    default_instructor = str(course_root) if course_root else os.getcwd()
    instructor_root = Path(ask(
        "Path to instructor repo root",
        default=default_instructor,
        completer=PathCompleter() if HAS_PROMPT_TOOLKIT else None,
        context=f"Should contain dist/{assignment_slug}/student/"
    )).expanduser().resolve()

    # Check if dist exists
    student_payload = instructor_root / "dist" / assignment_slug / "student"
    if not student_payload.exists():
        err(f"Student payload not found at: {student_payload}")
        print("Make sure you've run 'otter assign' first!")
        sys.exit(1)
    ok(f"Found student payload: {student_payload}")

    # Base directory for cloned repos
    gh_dir_default = config.get('gh_assignments_dir', '../gh-assignments-repos')
    if course_root:
        gh_dir_absolute = (course_root / gh_dir_default).resolve()
    else:
        gh_dir_absolute = Path(gh_dir_default).expanduser().resolve()

    base_dir = Path(ask(
        "Directory for cloned assignment repos",
        default=str(gh_dir_absolute),
        completer=PathCompleter() if HAS_PROMPT_TOOLKIT else None,
        context="Where to clone the new GitHub repo locally"
    )).expanduser().resolve()

    # Private repo?
    private_repo = yesno("Make the repository PRIVATE?", default_yes=True)

    # Construct repo name
    name_slug = sanitize_slug(assignment_name)
    repo_name = f"{assignment_slug}--{name_slug}" if name_slug != assignment_slug else assignment_slug

    print()
    say("Summary")
    print(f"  Organization:  {BOLD}{org}{RESET}")
    print(f"  Repo name:     {BOLD}{repo_name}{RESET}")
    print(f"  Display name:  {BOLD}{assignment_name}{RESET}")
    print(f"  Slug:          {BOLD}{assignment_slug}{RESET}")
    print(f"  Private:       {BOLD}{'Yes' if private_repo else 'No'}{RESET}")
    print(f"  Clone to:      {BOLD}{base_dir / assignment_slug}{RESET}")
    print()

    if not yesno("Proceed with these settings?", default_yes=True):
        warn("Aborted by user.")
        sys.exit(0)

    # Create or reuse repo
    if repo_exists(org, repo_name):
        warn(f"Repository {org}/{repo_name} already exists. Will reuse.")
    else:
        create_repo(org, repo_name, private=private_repo, description=f"Starter for {assignment_name}")

    set_repo_template(org, repo_name, is_template=True)

    # Clone repo
    target_dir = base_dir / assignment_slug
    if target_dir.exists() and any(target_dir.iterdir()):
        warn(f"Target directory exists and is non-empty: {target_dir}")
        if not yesno("Overwrite contents?", default_yes=False):
            warn("Skipping overwrite - assuming repo is already cloned and ready.")
            # Continue without cloning - assume it's already set up
        else:
            # Overwrite by removing and re-cloning
            import shutil
            shutil.rmtree(target_dir)
            clone_repo(org, repo_name, target_dir)
    else:
        clone_repo(org, repo_name, target_dir)

    # Copy student files
    copy_student_payload(instructor_root, assignment_slug, target_dir)

    # Manual steps - show early so user sees them
    say("Next Steps")
    print_classroom_instructions(classroom_url, org, repo_name, assignment_name)
    print_gradescope_reminder(assignment_slug, assignment_name)

    # Commit and push
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    git_commit_push(target_dir, f"Add starter files for {assignment_name} ({assignment_slug}) @ {ts}")

    # Save config
    new_config = {
        'last_classroom_name': classroom_name if 'classroom_name' in locals() else config.get('last_classroom_name'),
        'last_classroom_id': classroom_id if classroom_id else config.get('last_classroom_id'),
        'last_org': org,
        'gh_assignments_dir': get_relative_or_absolute(base_dir, course_root) if course_root else str(base_dir),
        'instructor_repo_root': get_relative_or_absolute(instructor_root, course_root) if course_root else str(instructor_root)
    }
    if course_root:
        save_config(course_root, new_config)

    # Show plan if dry run
    if DRY_RUN:
        print_plan()

    ok("Assignment bootstrap complete!")
    print(f"\n{BOLD}Template repo:{RESET} {CYAN}https://github.com/{org}/{repo_name}{RESET}")
    print(f"  1. Create Classroom assignment (see instructions above)")
    print(f"  2. Upload autograder to Gradescope")
    print(f"  3. Link assignment in your course tracker")
    print(f"\n{BOLD}Template repo:{RESET} {CYAN}https://github.com/{org}/{repo_name}{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user.{RESET}")
        sys.exit(130)
    except Exception as e:
        err(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
