#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import webbrowser

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"

DRY_RUN = False
PLAN = []  # list of dicts: {"type": "MANUAL"|"AUTO", "desc": str, "cmd": str|None, "url": str|None}

def add_plan(step_type, desc, cmd=None, url=None):
    PLAN.append({"type": step_type, "desc": desc, "cmd": cmd, "url": url})

def sh(cmd, check=True, capture_output=True, text=True):
    cmd_str = " ".join(cmd)
    if DRY_RUN:
        print(f"{YELLOW}[DRY RUN]{RESET} {cmd_str}")
        add_plan("AUTO", f"Execute: {cmd_str}", cmd=cmd_str)
        class Dummy:
            returncode = 0
            stderr = ""
        return Dummy()
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=text)

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

def pause(msg="Press ENTER to continue…"):
    input(f"{DIM}{msg}{RESET}")

def require_gh():
    if DRY_RUN:
        ok("Skipping gh auth check (dry run).")
        add_plan("AUTO", "Verify gh authentication", cmd="gh auth status")
        return
    if shutil.which("gh") is None:
        err("GitHub CLI (gh) is not installed.")
        print("Install from https://github.com/cli/cli and run: gh auth login")
        sys.exit(1)
    try:
        sh(["gh", "auth", "status"])
        ok("GitHub CLI authentication looks good.")
    except subprocess.CalledProcessError as e:
        err("GitHub CLI not authenticated.")
        print(e.stderr.strip())
        print("Run: gh auth login")
        sys.exit(1)

def org_exists(org):
    try:
        sh(["gh", "api", f"/orgs/{org}"])
        return True
    except subprocess.CalledProcessError:
        return False

def ensure_org(org):
    say("Organization check", f"Looking for org: {org}")
    if org_exists(org):
        ok(f"Org '{org}' exists.")
        return
    warn(f"Org '{org}' not found.")
    create_url = "https://github.com/organizations/plan"
    add_plan("MANUAL", f"Create GitHub organization '{org}' (Free plan is fine).", url=create_url)
    say("Manual step: Create the organization",
        "Choose the Free plan; we'll upgrade next.")
    print(f"URL: {create_url}")
    pause("Create the org, then press ENTER…")
    if not org_exists(org):
        err(f"Still can't find org '{org}'. Did you create it correctly?")
        sys.exit(1)
    ok(f"Org '{org}' now exists.")

def apply_education_upgrade():
    dash = "https://education.github.com/globalcampus/teacher"
    add_plan("MANUAL", "Apply/confirm Education upgrade (Upgrade to Team) for the org via Global Campus dashboard.", url=dash)
    say("Manual step: Apply GitHub Education upgrade",
        "Go to the Global Campus teacher dashboard → 'Upgrade your academic organizations'.")
    print(f"URL: {dash}")
    pause("After upgrading the target org to Team via the dashboard, press ENTER…")
    ok("Continuing.")

def create_classroom():
    url = "https://classroom.github.com/"
    add_plan("MANUAL", "Create a GitHub Classroom bound to the org; name it as prompted.", url=url)
    say("Manual step: Create a GitHub Classroom for this org",
        "In the UI: New classroom → select your org → name it appropriately.")
    print(f"URL: {url}")
    pause("After the classroom exists, press ENTER…")
    ok("Continuing.")

def create_team(org, name):
    cmd = ["gh", "api", "-X", "POST", f"/orgs/{org}/teams", "-f", f"name={name}", "-f", "privacy=closed"]
    add_plan("AUTO", f"Create team '{name}'", cmd=" ".join(cmd))
    try:
        sh(cmd)
        ok(f"Team created: {name}")
    except subprocess.CalledProcessError as e:
        if "name already exists" in e.stderr.lower():
            warn(f"Team already exists: {name}")
        else:
            warn(f"Couldn't create team '{name}' (continuing): {e.stderr.strip()}")

def set_codespaces_access(org, policy, selected_usernames=None):
    valid_policies = ("all_members_and_outside_collaborators", "all_members", "selected_members", "disabled")
    if policy not in valid_policies:
        raise ValueError(f"policy must be one of: {', '.join(valid_policies)}")
    cmd = ["gh", "api", "-X", "PUT", f"/orgs/{org}/codespaces/access", "-f", f"visibility={policy}"]
    add_plan("AUTO", f"Set Codespaces access policy to '{policy}'", cmd=" ".join(cmd))
    say("Codespaces access policy", f"Setting policy = {policy}")
    try:
        sh(cmd)
        ok("Codespaces policy updated.")
    except subprocess.CalledProcessError as e:
        warn(f"Could not set Codespaces policy ({e.stderr.strip()})")

    if policy == "selected_members":
        selected_usernames = selected_usernames or []
        if selected_usernames:
            cmd2 = ["gh", "api", "-X", "POST", f"/orgs/{org}/codespaces/access/users",
                    "-f", f"usernames={','.join(selected_usernames)}"]
            add_plan("AUTO", f"Add selected members for Codespaces: {', '.join(selected_usernames)}", cmd=" ".join(cmd2))
            try:
                sh(cmd2)
                ok("Selected members added for Codespaces.")
            except subprocess.CalledProcessError as e:
                warn(f"Could not add selected members ({e.stderr.strip()})")

def set_codespaces_ownership(org):
    say("Codespaces ownership", "Setting codespaces to be organization-owned")
    # Try to set via API (may not be available in all GitHub versions)
    cmd = ["gh", "api", "-X", "PATCH", f"/orgs/{org}/codespaces/default-setup", "-f", "codespace_as_default=false"]
    add_plan("AUTO", "Set codespaces to organization ownership", cmd=" ".join(cmd))
    try:
        sh(cmd)
        ok("Codespaces set to organization ownership.")
    except subprocess.CalledProcessError as e:
        warn(f"Could not set ownership via API ({e.stderr.strip()})")
        add_plan("MANUAL", "Set Codespaces ownership to organization", url=f"https://github.com/organizations/{org}/settings/codespaces/general")
        say("Manual step: Set codespaces ownership",
            "The API may not support this yet. Go to your org settings:")
        print(f"  1. URL: https://github.com/organizations/{org}/settings/codespaces/general")
        print("  2. Scroll to 'Codespace ownership'")
        print("  3. Select 'Organization ownership'")
        print("  4. Click Save")
        pause("After setting ownership, press ENTER…")
        ok("Continuing.")

def set_codespaces_spending_limit(org, amount):
    say("Codespaces spending limit", f"Setting spending budget to ${amount}")
    # Try to set spending limit via billing API
    cmd = ["gh", "api", "-X", "PATCH", f"/orgs/{org}/settings/billing/shared-storage-budget-alert-limit",
           "-f", f"alert_limit={int(amount * 100)}"]
    add_plan("AUTO", f"Set Codespaces spending limit to ${amount}", cmd=" ".join(cmd))
    try:
        sh(cmd)
        ok(f"Spending limit set to ${amount}.")
    except subprocess.CalledProcessError as e:
        warn(f"Could not set spending limit via API ({e.stderr.strip()})")
        add_plan("MANUAL", f"Set Codespaces spending budget to ${amount}", url=f"https://github.com/organizations/{org}/settings/billing")
        say("Manual step: Set spending budget",
            "The API may not support this endpoint. Go to your org billing settings:")
        print(f"  1. URL: https://github.com/organizations/{org}/settings/billing")
        print("  2. Look for 'Codespaces spending limit' or 'GitHub Codespaces' under metered services")
        print(f"  3. Set the spending limit to ${amount}")
        print("  4. Click Save")
        pause("After setting the spending limit, press ENTER…")
        ok("Continuing.")

def print_plan():
    if not PLAN:
        return
    print()
    say("Dry-run checklist (no changes made)")
    for i, step in enumerate(PLAN, 1):
        tag = "🧭 MANUAL" if step["type"] == "MANUAL" else "⚙️  AUTO"
        print(f"{i:2d}. {tag} — {step['desc']}")
        if step.get("url"):
            print(f"    ↳ URL: {step['url']}")
        if step.get("cmd"):
            print(f"    ↳ CMD: {step['cmd']}")
    print()

def sanitize_slug(s: str) -> str:
    import re
    s = s.strip().lower()
    s = s.replace(" ", "-").replace("_", "-")
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")

def ask_inputs():
    # Policy mapping: pretty name → GitHub API value
    POLICY_MAP = {
        "1": ("Everyone (members & outside collaborators)", "all_members_and_outside_collaborators"),
        "2": ("Members only", "all_members"),
        "3": ("Selected members only", "selected_members"),
        "4": ("Disabled", "disabled"),
    }

    org = ask("Enter the organization slug you want to use (e.g., bu-cds-ds100-f25)")
    classname = ask('Enter the classroom name you will use in the UI (e.g., "DS-100 (Fall 2025)")')
    say("Codespaces access policy")
    for key, (display, _) in POLICY_MAP.items():
        print(f"  {key}) {display}")
    choice = ask("Choose 1, 2, 3, or 4", default="1", validator=lambda x: x in POLICY_MAP)
    _, policy = POLICY_MAP[choice]
    selected_users = []
    if policy == "selected_members":
        users = ask("Enter comma-separated GitHub usernames to allow (or leave blank for none)", default="")
        selected_users = [u.strip() for u in users.split(",") if u.strip()]
    return org, classname, policy, selected_users

def ensure_org_wrapper(org):
    ensure_org(org)

def main():
    global DRY_RUN
    if "-n" in sys.argv or "--dry-run" in sys.argv:
        DRY_RUN = True
        warn("Running in DRY RUN mode (no changes will be made).")
        sys.argv = [a for a in sys.argv if a not in ("-n","--dry-run")]

    print()
    say("GitHub Education Bootstrapper (Interactive, No-Open URLs)")

    require_gh()

    org, classname, policy, selected_users = ask_inputs()

    ensure_org_wrapper(org)

    if yesno("Do you want to apply/confirm the Education (Team) upgrade now?"):
        apply_education_upgrade()
    else:
        warn("Skipping Education upgrade prompt (you can do it later).")

    if yesno("Do you want to create/confirm the GitHub Classroom now?"):
        create_classroom()
    else:
        warn("Skipping Classroom creation prompt (you can do it later).")

    if yesno("Create core teams 'instructors' and 'tas'?", default_yes=True):
        create_team(org, "instructors")
        create_team(org, "tas")
    else:
        warn("Skipping team creation.")

    set_codespaces_access(org, policy, selected_usernames=selected_users)

    if yesno("Configure Codespaces ownership and spending limit?", default_yes=True):
        set_codespaces_ownership(org)
        set_codespaces_spending_limit(org, 5)
    else:
        warn("Skipping Codespaces configuration (you can do it later in org settings).")

    print()
    say("Useful links (bookmark these):")
    print("  • Global Campus Teacher Dashboard: https://education.github.com/globalcampus/teacher")
    print("  • GitHub Classroom:               https://classroom.github.com/")
    print(f"  • Org settings (general):         https://github.com/organizations/{org}")
    print(f"  • Org people:                     https://github.com/orgs/{org}/people")
    print(f"  • Org billing:                    https://github.com/organizations/{org}/settings/billing")

    if DRY_RUN:
        print_plan()

    print()
    ok("Interactive bootstrap flow complete.")
    if DRY_RUN:
        warn("This was a dry run: no API calls were executed.")

if __name__ == "__main__":
    main()
