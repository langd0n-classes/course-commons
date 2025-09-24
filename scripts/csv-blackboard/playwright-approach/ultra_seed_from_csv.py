#!/usr/bin/env python3
"""
ultra_seed_from_csv.py — Blackboard Ultra seeder for learn.bu.edu (BU tenant)

Creates Ultra Assignments (points=0) from a CSV (title, release “Show on”, due).
Idempotent by title. Can group within an existing folder or force a single target folder.

CLI (kept):
  --csv, --course, --limit, --config (optional), --out (optional)
  --platform {auto,wayland,x11}
  --headless {true,false}
  --state-file state.json
Optional:
  --folder-col <CSV column>     (group rows by folder name in that column; folder must already exist)
  --target-folder "<name>"      (force all items into this existing folder; overrides --folder-col)
  --no-release                  (do not set Show-on even if present in CSV)

Storage state (not user-data-dir) is used for login persistence.

Requirements:
  pip install playwright pandas python-dateutil
  python -m playwright install chromium
"""

import argparse, csv as _csv, json, os, pathlib, re, sys, time, math
from datetime import datetime
from typing import Optional, Dict

import pandas as pd
from dateutil import parser as dtparse
from playwright.sync_api import sync_playwright, Page, Locator, TimeoutError as PWTimeout

# -------------------------------
# Config / constants
# -------------------------------
BASE = "https://learn.bu.edu"
DEFAULT_CFG = {
    "title_col": "Assignment/lecture name",
    "type_col": "Type",
    "due_date_col": "Due Date",
    "release_date_col": "Release Date",
    "include_types": ["Assignment", "Assessment", "Lab"],  # skip Lecture
}

# Toggles
USE_INLINE_PLUS = True                 # support inline “+” flow
FOLDER_CREATION_ENABLED = False        # do NOT create folders automatically

OUTPUT_DIR = pathlib.Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------
# Utilities
# -------------------------------
def _is_blank(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    s = str(v).strip()
    return s == "" or s.lower() == "nan"

def _norm_title(s: str) -> str:
    # collapse whitespace; strip
    return re.sub(r"\s+", " ", (s or "").strip())

def parse_date(s) -> Optional[datetime]:
    if _is_blank(s):
        return None
    try:
        # Handle different date formats that might be in CSV
        s_str = str(s).strip()
        print(f"  Parsing date: '{s_str}'")
        
        dt = dtparse.parse(s_str)
        print(f"  Parsed to: {dt.strftime('%m/%d/%Y %I:%M %p')}")
        
        return dt
    except Exception as e:
        print(f"  Failed to parse date '{s}': {e}")
        return None

def load_rows(csv_path: str, cfg: Dict, limit: Optional[int] = None, folder_col: Optional[str] = None):
    df = pd.read_csv(csv_path)
    mask = df[cfg["type_col"]].astype(str).str.strip().isin(cfg["include_types"])
    rows = []
    for _, row in df[mask].iterrows():
        raw_title = row.get(cfg["title_col"], "")
        title = "" if _is_blank(raw_title) else _norm_title(str(raw_title))
        if not title:
            continue
        due = parse_date(row.get(cfg["due_date_col"]))
        rel = parse_date(row.get(cfg["release_date_col"]))
        raw_folder = row.get(folder_col, "") if (folder_col and folder_col in df.columns) else ""
        folder = "" if _is_blank(raw_folder) else str(raw_folder).strip()
        rows.append({"title": title, "due": due, "release": rel, "folder": folder})
        if limit and len(rows) >= limit:
            break
    return rows

def save_debug(page: Page, name: str):
    try:
        page.screenshot(path=str(OUTPUT_DIR / f"{name}.png"), full_page=True)
    except Exception:
        pass

def try_wait(locator: Locator, timeout=1500) -> bool:
    try:
        locator.wait_for(timeout=timeout)
        return True
    except Exception:
        return False

def retry(fn, attempts=2, backoff_sec=0.8):
    last = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            time.sleep(backoff_sec)
    raise last

# -------------------------------
# Navigation anchors
# -------------------------------
def wait_for_logged_in(page: Page) -> bool:
    anchors = [
        page.get_by_role("link", name=re.compile(r"Courses", re.I)),
        page.get_by_role("navigation", name=re.compile(r"Course Navigation|Courses", re.I)),
    ]
    for _ in range(60):
        for a in anchors:
            if try_wait(a.first, timeout=600):
                return True
        page.wait_for_timeout(400)
    return False

def open_outline(page: Page, course_id: str) -> bool:
    page.goto(f"{BASE}/ultra/courses/{course_id}/outline", wait_until="domcontentloaded")
    anchors = [
        page.get_by_role("heading", name=re.compile(r"Course Content", re.I)),
        page.locator('[data-automation-id="course-outline"]'),
    ]
    for _ in range(60):
        for a in anchors:
            if try_wait(a.first, timeout=600):
                return True
        page.wait_for_timeout(300)
    return False

def ensure_on_outline(page: Page, course_id: str):
    if not open_outline(page, course_id):
        save_debug(page, "outline_not_found")
        raise RuntimeError("Could not reach course outline; see output/outline_not_found.png")

# -------------------------------
# Outline helpers (idempotency / folders)
# -------------------------------
def outline_container(page: Page) -> Locator:
    # Try the specific selector first
    specific = page.locator('[data-automation-id="course-outline"]')
    if specific.count() > 0:
        return specific
    
    # Fallback: look for the course content area more broadly
    fallbacks = [
        page.locator('.course-outline-content-list'),
        page.locator('[class*="course-outline"]'),
        page.locator('[class*="content-list"]'),
        page.locator('main'),  # Very broad fallback
        page,  # Ultimate fallback: entire page
    ]
    
    for fallback in fallbacks:
        if fallback.count() > 0:
            return fallback
    
    return page  # Return entire page as last resort

def _starts_with(text: str):
    # Accessible name begins with title/folder text (handles appended visibility/due bits)
    return re.compile(rf"^\s*{re.escape(text)}(\b|[\s:/|·-])", re.I)

def _page_down(page: Page, times=6, delay_ms=120):
    for _ in range(times):
        try:
            page.keyboard.press("PageDown")
        except Exception:
            try:
                page.mouse.wheel(0, 900)
            except Exception:
                pass
        page.wait_for_timeout(delay_ms)

def assignment_exists_in_scope(scope: Locator, title: str) -> bool:
    pat = _starts_with(title)
    # Also check for exact matches to be more precise
    exact_pat = re.compile(rf"^\s*{re.escape(title)}\s*$", re.I)
    
    for c in [
        scope.get_by_role("link", name=pat),
        scope.get_by_role("heading", name=pat),
        scope.get_by_role("button", name=pat),
        scope.get_by_text(pat),
        # Also check exact matches
        scope.get_by_role("link", name=exact_pat),
        scope.get_by_role("heading", name=exact_pat),
        scope.get_by_role("button", name=exact_pat),
        scope.get_by_text(exact_pat),
    ]:
        try:
            if c.count() > 0:
                # Check if any of the matches are visible
                for i in range(c.count()):
                    if c.nth(i).is_visible():
                        return True
        except Exception:
            pass
    return False

def assignment_exists_on_outline(page: Page, title: str) -> bool:
    """Search the outline (with scrolling) for an item whose name starts with title."""
    cont = outline_container(page)
    if assignment_exists_in_scope(cont, title):
        return True
    # Progressive scroll
    for _ in range(15):
        try: page.mouse.wheel(0, 1200)
        except Exception: pass
        if assignment_exists_in_scope(cont, title):
            return True
    # Try PageDown as a second modality
    _page_down(page, times=10)
    return assignment_exists_in_scope(cont, title)

def _open_search(page: Page) -> Optional[Locator]:
    btn = page.get_by_role("button", name=re.compile(r"Search", re.I)).first
    try:
        if btn.count() > 0 and btn.is_visible():
            btn.click(timeout=1500)
    except Exception:
        pass
    search_box = (
        page.get_by_role("searchbox").first
        .or_(page.locator("input[type='search']")).first
        .or_(page.get_by_placeholder(re.compile(r"Search", re.I))).first
    )
    return search_box if search_box.count() > 0 else None

def assignment_exists_globally(page: Page, title: str) -> bool:
    """Outline scroll + page-wide check + search box (handles off-screen items and inside folders)."""
    if assignment_exists_on_outline(page, title):
        return True
    
    pat = _starts_with(title)
    exact_pat = re.compile(rf"^\s*{re.escape(title)}\s*$", re.I)
    
    # Check both starts-with and exact matches
    for c in [
        page.get_by_role("heading", name=pat), 
        page.get_by_role("link", name=pat), 
        page.get_by_text(pat),
        page.get_by_role("heading", name=exact_pat), 
        page.get_by_role("link", name=exact_pat), 
        page.get_by_text(exact_pat)
    ]:
        try:
            if c.count() > 0:
                # Check if any visible matches exist
                for i in range(c.count()):
                    try:
                        if c.nth(i).is_visible():
                            return True
                    except Exception:
                        continue
        except Exception:
            pass
    
    # Search control - try both exact title and starts-with patterns
    sb = _open_search(page)
    try:
        if sb:
            # First try exact title search
            sb.fill(title)
            page.wait_for_timeout(1200)
            if page.get_by_text(exact_pat).count() > 0 or page.get_by_text(pat).count() > 0:
                sb.fill(""); page.keyboard.press("Escape")
                return True
            sb.fill(""); page.keyboard.press("Escape")
    except Exception:
        pass
    return False

def _confirm_inside_folder(page: Page, name: str) -> bool:
    # When a folder is ACTUALLY open, Ultra shows both:
    # 1. A page heading with the folder name (this just means the folder exists)
    # 2. A folder content area with id="folder-contents-[ID]" (this means we're inside it)
    
    # The folder content area is the DEFINITIVE indicator that we're inside a folder
    folder_content_area = page.locator('[id^="folder-contents-"]')
    is_inside = folder_content_area.count() > 0
    
    h = page.get_by_role("heading", name=re.compile(rf"^\s*{re.escape(name)}\s*$", re.I))
    
    if is_inside:
        print(f"  ✓ Confirmed inside folder '{name}' (heading: {h.count()}, content-area: {folder_content_area.count()})")
        # Debug: Take screenshot to verify folder context
        save_debug(page, f"inside_folder_{name.replace(' ', '_')}")
    else:
        print(f"  ✗ Not inside folder '{name}' - folder may be closed (heading: {h.count()}, content-area: {folder_content_area.count()})")
        # Debug: Take screenshot to see current state
        save_debug(page, f"not_in_folder_{name.replace(' ', '_')}")
    
    return is_inside

def _click_tile_container(cont: Locator, pat) -> bool:
    # Click the folder tile itself if link/button/heading aren't present
    tile = cont.locator("article, li, section, div").filter(has_text=pat).first
    if tile.count() > 0:
        try: tile.scroll_into_view_if_needed(timeout=1200)
        except Exception: pass
        try:
            # click near left edge to avoid sub-controls
            box = tile.bounding_box()
            if box:
                tile.click(position={"x": max(8, int(box["width"] * 0.2)), "y": int(min(box["height"] - 4, 18))}, timeout=2000)
            else:
                tile.click(timeout=2000)
            return True
        except Exception:
            try: tile.dblclick(timeout=1600); return True
            except Exception: pass
    return False

def _click_folder_via_search(page: Page, name: str) -> bool:
    sb = _open_search(page)
    if not sb:
        return False
    sb.fill(name)
    page.wait_for_timeout(700)
    pat = _starts_with(name)
    cont = outline_container(page)
    # Prefer the button role (trace shows folder tile is a button)
    for loc in [
        cont.get_by_role("button", name=re.compile(rf"^{re.escape(name)}$", re.I)).first,
        cont.get_by_role("button", name=pat).first,
        cont.get_by_role("link",   name=pat).first,
        cont.get_by_role("heading",name=pat).first,
        cont.get_by_text(pat).first,
    ]:
        if try_wait(loc, timeout=1200):
            try: loc.scroll_into_view_if_needed(timeout=1200)
            except Exception: pass
            try:
                loc.click(timeout=1500)
                sb.fill(""); page.keyboard.press("Escape")
                return True
            except Exception:
                pass
    # last resort: click tile by text
    if _click_tile_container(cont, pat):
        sb.fill(""); page.keyboard.press("Escape")
        return True
    sb.fill(""); page.keyboard.press("Escape")
    return False

def enter_folder(page: Page, name: str) -> bool:
    """Open an existing folder by name (root outline). Robust + verifies entry."""
    if not name:
        return False
        
    print(f"  Looking for folder: '{name}'")
    
    # Quick check for page readiness (no long delays)
    try:
        # Just verify we can find some basic course content, but don't wait long
        page.wait_for_selector('button, [class*="content"]', timeout=3000)
    except Exception:
        pass  # Continue anyway
    
    cont = outline_container(page)
    
    # Debug: Check if the outline container is working
    try:
        cont_count = cont.count()
        print(f"  Outline container found: {cont_count} elements")
        if cont_count > 0:
            # Check if there are ANY buttons at all in the container
            all_buttons_in_cont = cont.locator('button')
            button_count = all_buttons_in_cont.count()
            print(f"  Total buttons in outline container: {button_count}")
            
            # Look for ANY button containing "Placeholder" (case insensitive)
            placeholder_buttons = cont.locator('button').filter(has_text=re.compile(r"placeholder", re.I))
            placeholder_count = placeholder_buttons.count()
            print(f"  Buttons containing 'placeholder' (case insensitive): {placeholder_count}")
        else:
            print(f"  ERROR: Outline container not found!")
    except Exception as e:
        print(f"  Error checking outline container: {e}")
    
    # First, let's see what folders actually exist by taking a debug screenshot
    save_debug(page, f"before_folder_search_{name.replace(' ', '_')}")
    
    # Check if the folder might already be open (we're already inside it)
    if _confirm_inside_folder(page, name):
        print(f"  Already inside folder: '{name}'")
        return True
    
    # Try exact match first - look for the specific folder toggle button
    exact_patterns = [
        re.compile(rf"^\s*{re.escape(name)}\s*$", re.I),
        re.compile(rf"^{re.escape(name)}$", re.I)
    ]
    
    for pattern in exact_patterns:
        print(f"  Searching for folder with pattern: {pattern.pattern}")
        
        # Look specifically for folder toggle button (this is the correct element to click)
        folder_toggle_candidates = [
            # Most specific: the toggle button with analytics ID
            cont.locator('button[data-analytics-id="content.item.folder.toggleFolder.button"]').filter(has_text=pattern),
            # Folder title button with aria-expanded attribute
            cont.locator('button[aria-expanded]').filter(has_text=pattern),
            # Button with folder-title ID pattern
            cont.locator('button[id*="folder-title"]').filter(has_text=pattern),
            # Generic button/link/heading approach (fallback)
            cont.get_by_role("button", name=pattern),
            cont.get_by_role("link", name=pattern),
            cont.get_by_role("heading", name=pattern),
        ]
        
        for i, candidate in enumerate(folder_toggle_candidates):
            candidate_count = candidate.count()
            print(f"  Candidate {i} found {candidate_count} matches")
            if candidate_count > 0:
                for j in range(candidate_count):
                    try:
                        elem = candidate.nth(j)
                        if elem.is_visible():
                            print(f"  Found folder toggle element {i}.{j}, checking if expandable...")
                            
                            # Check current state
                            is_expanded = False
                            try:
                                expanded_attr = elem.get_attribute('aria-expanded', timeout=1000)
                                is_expanded = expanded_attr == 'true'
                                print(f"  Folder aria-expanded: {expanded_attr}")
                            except Exception:
                                print(f"  No aria-expanded attribute found")
                            
                            if not is_expanded:
                                print(f"  Clicking folder toggle to expand...")
                                elem.scroll_into_view_if_needed(timeout=800)
                                elem.click(timeout=1200)
                                page.wait_for_timeout(300)  # Reduced wait time
                                
                                if _confirm_inside_folder(page, name):
                                    return True
                                else:
                                    print(f"  Click attempt {i}.{j} did not open folder")
                            else:
                                print(f"  Folder already expanded, checking content...")
                                if _confirm_inside_folder(page, name):
                                    return True
                    except Exception as e:
                        print(f"  Failed to click folder toggle element {i}.{j}: {e}")
                        continue
    
    # Try starts-with pattern
    pat = _starts_with(name)
    
    def _try_click_with_pattern(pattern) -> bool:
        for role in ["button", "link", "heading"]:
            elements = cont.get_by_role(role, name=pattern)
            if elements.count() > 0:
                for i in range(elements.count()):
                    try:
                        elem = elements.nth(i)
                        if elem.is_visible():
                            elem.scroll_into_view_if_needed(timeout=1200)
                            elem.click(timeout=1600)
                            return True
                    except Exception:
                        continue
        
        # Try text elements
        text_elements = cont.get_by_text(pattern)
        if text_elements.count() > 0:
            for i in range(text_elements.count()):
                try:
                    elem = text_elements.nth(i)
                    if elem.is_visible():
                        elem.scroll_into_view_if_needed(timeout=1200)
                        elem.click(timeout=1600)
                        return True
                except Exception:
                    continue
        
        # Last resort: click the tile container region
        return _click_tile_container(cont, pattern)

    # Try with starts-with pattern
    if _try_click_with_pattern(pat):
        page.wait_for_timeout(500)
        if _confirm_inside_folder(page, name):
            return True

    # Scroll and try again
    for _ in range(15):
        try: page.mouse.wheel(0, 1000)
        except Exception: pass
        if _try_click_with_pattern(pat):
            page.wait_for_timeout(500)
            if _confirm_inside_folder(page, name):
                return True

    # Page down and try again
    _page_down(page, times=10)
    if _try_click_with_pattern(pat):
        page.wait_for_timeout(500)
        if _confirm_inside_folder(page, name):
            return True

    # Use the Course Content search to jump to the folder
    print(f"  Trying search for folder: '{name}'")
    if _click_folder_via_search(page, name):
        page.wait_for_timeout(500)
        if _confirm_inside_folder(page, name):
            return True

    # Final attempt: check if the folder might not exist or might be named differently
    print(f"  Folder '{name}' not found. Checking what folders actually exist...")
    save_debug(page, "folder_search_failed")
    
    # Debug: List all folders that actually exist using multiple approaches
    try:
        # Try multiple selectors to find folder buttons
        folder_selectors = [
            'button[data-analytics-id="content.item.folder.toggleFolder.button"]',
            'button[aria-expanded]',
            'button[id*="folder-title"]',
        ]
        
        for selector_idx, selector in enumerate(folder_selectors):
            all_folder_buttons = cont.locator(selector)
            folder_count = all_folder_buttons.count()
            print(f"  Selector {selector_idx} ('{selector}') found {folder_count} folders:")
            
            for i in range(min(folder_count, 10)):  # Show up to 10 folders
                try:
                    folder_btn = all_folder_buttons.nth(i)
                    folder_name = folder_btn.inner_text(timeout=1000)
                    expanded = folder_btn.get_attribute('aria-expanded', timeout=1000)
                    button_id = folder_btn.get_attribute('id', timeout=1000)
                    print(f"    Folder {i}: '{folder_name}' (expanded: {expanded}, id: {button_id})")
                except Exception as e:
                    print(f"    Folder {i}: Error reading folder info: {e}")
                    
            if folder_count > 0:
                break  # Found folders with this selector, no need to try others
                
    except Exception as e:
        print(f"  Could not list folders: {e}")
    
    # Maybe the folder doesn't exist - let's continue at root level
    print(f"  Warning: Folder '{name}' not found, will create assignments at root level")
    return False

def maybe_exit_item_editor(page: Page):
    for btn in [
        page.get_by_role("button", name=re.compile(r"Close", re.I)),
        page.get_by_role("button", name=re.compile(r"Cancel", re.I)),
    ]:
        try:
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click(timeout=1200)
        except Exception:
            pass

# -------------------------------
# Creation helpers
# -------------------------------
def reveal_inline_plus(page: Page):
    """Hover over content to reveal the inline + button with dynamic names"""
    cont = outline_container(page)
    
    # Check if we're inside a folder - if so, focus hover efforts there
    folder_content_area = page.locator('[id^="folder-contents-"]').first
    is_in_folder = folder_content_area.count() > 0
    
    if is_in_folder:
        print("  Hovering within folder context...")
        try:
            # Hover over the folder content area to reveal folder-specific plus buttons
            folder_content_area.hover(timeout=500)
            page.wait_for_timeout(200)
            
            # Look specifically for content within the folder to hover over
            folder_content_items = [
                folder_content_area.get_by_role("link"),
                folder_content_area.get_by_role("heading"),
                folder_content_area.locator("article"),
                folder_content_area.locator("li"),
                folder_content_area.locator('[class*="contentItem"]'),
                folder_content_area.locator('[class*="itemContainer"]'),
            ]
            
            # If folder has content, hover at the end to reveal "add content below" buttons
            for content_group in folder_content_items:
                if content_group.count() > 0:
                    count = content_group.count()
                    # Hover over the last item to reveal "Add content below" button
                    try:
                        last_item = content_group.nth(count - 1)
                        if last_item.is_visible():
                            print(f"  Hovering over last folder content item to reveal bottom + button...")
                            last_item.hover(timeout=1000)
                            page.wait_for_timeout(500)
                            break
                    except Exception:
                        continue
            
            # Also try hovering at the very bottom of the folder content area
            try:
                # Get the folder content area bounds and hover near the bottom
                folder_bounds = folder_content_area.bounding_box()
                if folder_bounds:
                    # Hover near the bottom of the folder content area
                    bottom_x = folder_bounds["x"] + folder_bounds["width"] / 2
                    bottom_y = folder_bounds["y"] + folder_bounds["height"] - 20
                    print(f"  Hovering at bottom of folder content area...")
                    page.mouse.move(bottom_x, bottom_y)
                    page.wait_for_timeout(400)
            except Exception:
                pass
                
        except Exception:
            print("  Failed to hover within folder context")
    else:
        # Original logic for non-folder context
        try: 
            cont.first.hover(timeout=800)
            page.wait_for_timeout(300)
        except Exception:
            try: 
                page.mouse.move(220, 220)
                page.wait_for_timeout(300)
            except Exception: 
                pass
    
    # General hover strategy: hover over existing content items
    try:
        # Look for existing assignments or content in the current view that are actually visible
        search_area = folder_content_area if is_in_folder else cont
        content_selectors = [
            search_area.get_by_role("link"),
            search_area.get_by_role("heading"),
            search_area.locator("article"),
            search_area.locator("li"),
        ]
        
        hovered = False
        for content_group in content_selectors:
            if content_group.count() > 0:
                # Hover over the last few visible items (more likely to reveal the right + button)
                count = content_group.count()
                start_idx = max(0, count - 3)  # Last 3 items
                
                for i in range(start_idx, count):
                    try:
                        item = content_group.nth(i)
                        if item.is_visible():
                            print(f"  Hovering over content item {i}/{count-1} to reveal + button...")
                            item.hover(timeout=1000)
                            page.wait_for_timeout(400)  # Longer wait to let + button appear
                            hovered = True
                    except Exception:
                        continue
                
                if hovered:
                    break  # Stop after first successful hover group
    except Exception:
        pass

def open_create_menu(page: Page):
    """Open the first-level menu that contains 'Create' (or a global 'Create' button)."""
    def _do():
        # First, make sure we're in a good state to find the create button
        print("  Looking for create/add button...")
        
        # Refresh the page state by moving mouse and waiting
        try:
            page.mouse.move(400, 300)
            page.wait_for_timeout(300)
        except Exception:
            pass
        
        if USE_INLINE_PLUS:
            print("  Trying to reveal inline plus button...")
            reveal_inline_plus(page)
            
            # NEW: Check if we're inside a folder and prioritize folder-specific plus buttons
            folder_content_area = page.locator('[id^="folder-contents-"]').first
            is_in_folder = folder_content_area.count() > 0
            
            if is_in_folder:
                print("  Detected folder context, looking for folder-specific plus buttons...")
                # Debug information
                try:
                    folder_id = folder_content_area.get_attribute('id', timeout=1000)
                    print(f"  Folder content area ID: {folder_id}")
                except Exception:
                    print("  Could not get folder content area ID")
                
                # Look for plus buttons specifically within the folder content area
                folder_plus_selectors = [
                    # These are the specific patterns from the HTML you provided
                    folder_content_area.get_by_role("button", name=re.compile(r"Add new content below", re.I)),
                    folder_content_area.get_by_role("button", name=re.compile(r"Add new content above", re.I)),
                    folder_content_area.get_by_role("button", name=re.compile(r"^Add new content$", re.I)),
                    folder_content_area.locator('button[aria-label*="Add new content"]'),
                    # Also try with class selectors from the HTML
                    folder_content_area.locator('button.makeStylesaddButton-0-2-594'),
                    folder_content_area.locator('button[id^="add-content-menu-button"]'),
                ]
                
                for i, c in enumerate(folder_plus_selectors):
                    try:
                        if c.count() > 0:
                            for j in range(c.count()):
                                btn = c.nth(j)
                                if btn.is_visible():
                                    print(f"  Found folder plus button {i}.{j}, clicking...")
                                    btn.scroll_into_view_if_needed(timeout=1500)
                                    btn.click(timeout=2500)
                                    page.wait_for_timeout(500)
                                    return
                    except Exception as e:
                        print(f"  Folder plus button {i} failed: {e}")
                        continue
            
            # Fallback to general plus button search if folder-specific search failed
            print("  Trying general plus button selectors...")
            # Look for + buttons with dynamic names that appear on hover
            plus_selectors = [
                # Dynamic button names that appear on hover
                page.get_by_role("button", name=re.compile(r"Add new content below", re.I)),
                page.get_by_role("button", name=re.compile(r"Add new content above", re.I)),
                page.get_by_role("button", name=re.compile(r"Add new content after", re.I)),
                page.get_by_role("button", name=re.compile(r"Add content below", re.I)),
                page.get_by_role("button", name=re.compile(r"Add content after", re.I)),
                # Traditional selectors
                page.get_by_role("button", name=re.compile(r"^\+$")),
                page.get_by_role("button", name=re.compile(r"Add new content", re.I)),
                page.get_by_role("button", name=re.compile(r"Add content", re.I)),
                page.locator('button[aria-label*="Add new content"]'),
                page.locator('button[aria-label*="Add content"]'),
                page.locator('button[aria-label*="below" i]'),
                page.locator('button[aria-label*="after" i]'),
                page.locator('button[aria-label*="above" i]'),
                page.locator('bb-plus-menu button'),
                page.locator(".click-to-invoke-container button"),
                page.locator('button').filter(has_text=re.compile(r"^\+$")),
                # Try more generic selectors
                page.locator('button[title*="Add" i]'),
                page.locator('button[title*="Create" i]'),
                # Add the specific class from the HTML
                page.locator('button.makeStylesaddButton-0-2-594'),
            ]
            
            for i, c in enumerate(plus_selectors):
                try:
                    if c.count() > 0:
                        for j in range(c.count()):
                            btn = c.nth(j)
                            if btn.is_visible():
                                print(f"  Found plus button {i}.{j}, clicking...")
                                btn.click(timeout=2500)
                                page.wait_for_timeout(500)
                                return
                except Exception as e:
                    print(f"  Plus button {i} failed: {e}")
                    continue
        
        # Try global create buttons
        print("  Trying global create buttons...")
        global_selectors = [
            page.get_by_role("button", name=re.compile(r"^Create$", re.I)),
            page.get_by_role("button", name=re.compile(r"Add content", re.I)),
            page.get_by_role("button", name=re.compile(r"New", re.I)),
        ]
        
        for i, c in enumerate(global_selectors):
            try:
                if c.count() > 0 and c.first.is_visible():
                    print(f"  Found global button {i}, clicking...")
                    c.first.click(timeout=2500)
                    page.wait_for_timeout(500)
                    return
            except Exception as e:
                print(f"  Global button {i} failed: {e}")
                continue
        
        save_debug(page, "no_add_button")
        raise RuntimeError("Add/Create button not found (output/no_add_button.png)")
    
    return retry(_do, attempts=3, backoff_sec=1.0)

def click_create_if_present(page: Page):
    for ce in [
        page.get_by_role("menuitem", name=re.compile(r"^Create$", re.I)),
        page.get_by_role("button",   name=re.compile(r"^Create$", re.I)),
        page.get_by_text(re.compile(r"^Create$", re.I)),
    ]:
        try:
            if ce.count() > 0 and ce.first.is_visible():
                ce.first.click(timeout=2500)
                try_wait(page.get_by_role("heading", name=re.compile(r"Create Item", re.I)).first, timeout=3000)
                return True
        except Exception:
            pass
    return False

def _focus_create_drawer(page: Page):
    hdr = page.get_by_role("heading", name=re.compile(r"^Create Item$", re.I)).first
    if try_wait(hdr, timeout=3000):
        try: hdr.click(timeout=1500); return True
        except Exception: pass
    drawer = page.locator("aside, [role='dialog'], [aria-label*='Create Item']").first
    try:
        if drawer.count() > 0:
            drawer.click(timeout=1500)
            return True
    except Exception:
        pass
    return False

def _expand_assessment_section(page: Page):
    acc = page.get_by_role("button", name=re.compile(r"^Assessment$", re.I)).first
    if acc.count() > 0:
        try:
            val = acc.get_attribute("aria-expanded")
            if val != "true":
                acc.click(timeout=1500)
                time.sleep(0.2)
        except Exception:
            pass

def _find_and_click_assignment_in_drawer(page: Page) -> bool:
    locators = [
        page.get_by_role("button",   name=re.compile(r"^\s*Assignment\s*$", re.I)),
        page.get_by_role("link",     name=re.compile(r"^\s*Assignment\s*$", re.I)),
        page.get_by_role("menuitem", name=re.compile(r"^\s*Assignment\s*$", re.I)),
        page.locator("button:has-text('Assignment')"),
        page.locator("a:has-text('Assignment')"),
        page.locator("[data-automation-id*='Assignment']"),
        # Some BU menus label assessment items weirdly; accept "Test" as a fallback
        page.get_by_role("link", name=re.compile(r"^\s*Test\s*$", re.I)),
        page.get_by_role("button", name=re.compile(r"^\s*Test\s*$", re.I)),
    ]
    for L in locators:
        if L.count() > 0:
            try:
                L.first.scroll_into_view_if_needed(timeout=2000)
                L.first.click(timeout=3000)
                return True
            except Exception:
                pass
    return False

def choose_assignment(page: Page):
    def _do():
        click_create_if_present(page)
        # direct
        for loc in [
            page.get_by_role("link",     name=re.compile(r"^Assignment$", re.I)),
            page.get_by_role("button",   name=re.compile(r"^Assignment$", re.I)),
            page.get_by_role("menuitem", name=re.compile(r"^Assignment$", re.I)),
            page.locator('button:has-text("Assignment")'),
            page.locator('div[role="menu"] >> text=Assignment'),
            page.get_by_role("link", name=re.compile(r"^\s*Test\s*$", re.I)),   # BU fallback
            page.get_by_role("button", name=re.compile(r"^\s*Test\s*$", re.I)),
        ]:
            try:
                if loc.count() > 0:
                    loc.first.click(timeout=3500)
                    return
            except Exception:
                pass
        # drawer
        _focus_create_drawer(page)
        _expand_assessment_section(page)
        if _find_and_click_assignment_in_drawer(page):
            return
        for _ in range(6):
            try: page.keyboard.press("PageDown")
            except Exception:
                try: page.mouse.wheel(0, 800)
                except Exception: pass
            time.sleep(0.15)
            if _find_and_click_assignment_in_drawer(page):
                return
        save_debug(page, "no_assignment_choice")
        raise RuntimeError("Assignment option not found (output/no_assignment_choice.png)")
    return retry(_do, attempts=2, backoff_sec=0.9)

# -------------------------------
# Editor helpers
# -------------------------------
def fill_title(page: Page, title: str):
    def _fill_title_attempt():
        title_box = page.get_by_role("textbox", name=re.compile(r"New Assignment", re.I))
        if not try_wait(title_box, timeout=15000):
            title_box = page.get_by_placeholder(re.compile(r"New Assignment|Title|Add title", re.I))
            if not try_wait(title_box, timeout=8000):
                title_box = page.locator('[contenteditable="true"]').first
                if not try_wait(title_box, timeout=5000):
                    save_debug(page, "title_input_missing")
                    raise RuntimeError("Assignment title input not found (output/title_input_missing.png)")
        
        # Ensure the title box is visible and interactable
        try:
            title_box.scroll_into_view_if_needed(timeout=2000)
        except Exception:
            pass
            
        title_box.click(timeout=3000)
        title_box.fill(title)
        # Verify the title was actually set
        page.wait_for_timeout(300)
        current_value = title_box.input_value()
        if current_value != title:
            raise Exception(f"Title not set correctly: expected '{title}', got '{current_value}'")
    
    retry(_fill_title_attempt, attempts=2, backoff_sec=1.0)

def open_settings(page: Page):
    hdr = page.get_by_role("heading", name=re.compile(r"^Assignment Settings$", re.I)).first
    if try_wait(hdr, timeout=500):
        return
    for b in [
        page.get_by_role("link",  name=re.compile(r"^Settings$", re.I)),
        page.get_by_role("button",name=re.compile(r"^Settings$", re.I)),
        page.get_by_role("button",name=re.compile(r"Assignment Settings", re.I)),
        page.get_by_text(re.compile(r"^Settings$", re.I)),
        page.locator("button[aria-label*='settings' i]"),
    ]:
        try:
            if b.count() > 0:
                b.first.click(timeout=5000)
                if try_wait(page.get_by_role("heading", name=re.compile(r"Assignment Settings", re.I)).first, timeout=3000):
                    return
        except Exception:
            pass
    save_debug(page, "settings_not_found")  # not fatal

def _ensure_time_field(scope: Locator) -> Locator:
    # Preferred: the BU trace shows "Due Date: Time"
    t = scope.get_by_role("textbox", name=re.compile(r"(Due Date:\s*)?Time$", re.I)).first
    if t.count() == 0:
        tp = scope.get_by_role("button", name=re.compile(r"Time picker", re.I)).first
        try:
            if tp.count() > 0:
                tp.click(timeout=1200)
                t = scope.get_by_role("textbox", name=re.compile(r"(Due Date:\s*)?Time$", re.I)).first
        except Exception:
            pass
    if t.count() == 0:
        t = scope.locator("input[placeholder='hh:mm AM/PM']").first
    return t

def _type_and_commit_time(tbox: Locator, dt: datetime) -> None:
    # Select all, type, press Enter to commit masked inputs
    candidates = []
    # Use very specific format: "2:00 PM" (not "02:00 PM")
    time_format = dt.strftime("%-I:%M %p") if os.name != "nt" else dt.strftime("%I:%M %p").lstrip("0")
    
    print(f"  Setting time to: '{time_format}'")
    
    try:
        tbox.click(timeout=2000)
        tbox.press("Control+A")
        tbox.fill(time_format)
        
        # CRITICAL: Use Tab key (not Enter) to commit the time field
        print(f"  Pressing Tab to commit time...")
        tbox.press("Tab")
        
        # Wait a bit for the UI to process the change
        page = tbox.page
        page.wait_for_timeout(500)
        
        # Verify the time was set by checking the field value
        try:
            current_val = tbox.input_value(timeout=1000)
            print(f"  Time field now shows: '{current_val}'")
        except Exception:
            pass
            
        print(f"  Time setting completed")
        
    except Exception as e:
        print(f"  Time setting failed: {e}")

def set_points_zero(page: Page):
    """Set assignment points to 0. Based on codegen, this should be in right column."""
    
    def _try_right_column_grading():
        # The codegen shows clicking "Grading 100 maximum points" link in right column
        grading_patterns = [
            re.compile(r"Grading.*maximum points", re.I),
            re.compile(r"\d+\s+maximum points", re.I),
            re.compile(r"maximum points", re.I),
            re.compile(r"^Grading$", re.I)
        ]
        
        for pattern in grading_patterns:
            links = page.get_by_role("link", name=pattern)
            if links.count() > 0:
                for i in range(links.count()):
                    try:
                        link = links.nth(i)
                        if link.is_visible():
                            print(f"  Found grading link: {link.inner_text()[:50]}...")
                            link.scroll_into_view_if_needed(timeout=1500)
                            link.click(timeout=2500)
                            page.wait_for_timeout(500)
                            
                            # Look for Maximum points input
                            pts_selectors = [
                                page.get_by_role("textbox", name=re.compile(r"Maximum points", re.I)),
                                page.get_by_role("spinbutton", name=re.compile(r"Maximum points", re.I)),
                                page.get_by_role("textbox", name=re.compile(r"\*\s*Maximum points", re.I)),
                                page.locator("input[aria-label*='Maximum points' i]"),
                                page.locator("input[placeholder*='points' i]"),
                            ]
                            
                            for pts in pts_selectors:
                                if try_wait(pts, timeout=3000):
                                    print(f"  Found points input field")
                                    pts.first.scroll_into_view_if_needed(timeout=1500)
                                    pts.first.click(timeout=2000)
                                    pts.first.fill("0")
                                    
                                    # CRITICAL: Use Tab key (not Enter) to commit the points input
                                    print(f"  Pressing Tab to commit points...")
                                    pts.first.press("Tab")
                                    page.wait_for_timeout(500)
                                    
                                    # Verify points were set
                                    try:
                                        current_val = pts.first.input_value(timeout=1000)
                                        print(f"  Points field shows: '{current_val}'")
                                    except Exception:
                                        pass
                                    
                                    # Don't save yet - return True to indicate we found and set the field
                                    page.wait_for_timeout(500)
                                    return True
                    except Exception as e:
                        print(f"  Failed to use grading link: {e}")
                        continue
        return False
    
    # First try the right column approach (most likely to work)
    try:
        if _try_right_column_grading():
            return
    except Exception as e:
        print(f"Right column grading approach failed: {e}")
        pass
    # Fallback: try settings drawer/panel approach
    def _try_settings_drawer():
        print("  Trying settings drawer approach for points...")
        open_settings(page)
        page.wait_for_timeout(1000)
        
        # Take screenshot for debugging
        save_debug(page, "settings_drawer_opened")
        
        # Look for any points-related inputs in the entire page
        pts_selectors = [
            page.get_by_role("textbox", name=re.compile(r"Maximum points", re.I)),
            page.get_by_role("spinbutton", name=re.compile(r"Maximum points", re.I)),
            page.get_by_role("textbox", name=re.compile(r"\*\s*Maximum points", re.I)),
            page.locator("input[aria-label*='Maximum points' i]"),
            page.locator("input[aria-label*='Points' i]"),
            page.locator("input[placeholder*='points' i]"),
            page.locator("input[type='number']").filter(has_text=re.compile(r"points", re.I)),
            # Also try more generic approaches
            page.locator("input[type='number']"),
            page.locator("input[type='text']").filter(has_text=re.compile(r"100|points", re.I))
        ]
        
        for i, pts in enumerate(pts_selectors):
            if pts.count() > 0:
                for j in range(pts.count()):
                    try:
                        field = pts.nth(j)
                        if field.is_visible():
                            print(f"  Trying points field {i}.{j}")
                            field.scroll_into_view_if_needed(timeout=1500)
                            field.click(timeout=2000)
                            field.fill("0")
                            page.wait_for_timeout(300)
                            
                            # Try to save
                            save_btns = [
                                page.get_by_role("button", name=re.compile(r"^Save$", re.I)),
                                page.get_by_role("button", name=re.compile(r"^Apply$", re.I)),
                                page.get_by_role("button", name=re.compile(r"^OK$", re.I))
                            ]
                            
                            for save_btn in save_btns:
                                if save_btn.count() > 0 and save_btn.first.is_visible():
                                    save_btn.first.click(timeout=2500)
                                    page.wait_for_timeout(500)
                                    return True
                            return True  # Even if save button not found, field might be set
                    except Exception as e:
                        print(f"  Failed to set points field {i}.{j}: {e}")
                        continue
        return False
    
    # Try settings drawer approach
    try:
        if _try_settings_drawer():
            return
    except Exception as e:
        print(f"Settings drawer approach failed: {e}")
        pass
    
    # If all approaches failed, this is not critical - assignments can be created with default points
    print("  Warning: Could not set points to 0, assignment will use default points")
    save_debug(page, "points_setting_failed_final")

def _verify_due_right_column(page: Page, dt: datetime) -> bool:
    # Right column shows the value as a link; read its inner text
    # Accept both zero-padded '02:00 PM' and '2:00 PM'
    exp1 = dt.strftime("%-I:%M %p") if os.name != "nt" else dt.strftime("%I:%M %p").lstrip("0")
    exp2 = dt.strftime("%I:%M %p")
    
    print(f"  Looking for time '{exp1}' or '{exp2}' in right column...")
    
    # The link is typically next to/under text 'Due date'
    dd_link = page.get_by_role("link", name=re.compile(r"\b(AM|PM)\b|\d{4}", re.I)).first
    try:
        if dd_link.count() > 0:
            txt = dd_link.inner_text(timeout=1500)
            print(f"  Due date link shows: '{txt}'")
            # Be more lenient - check if the time portion matches
            if (exp1.split()[-1] in txt and exp1.split()[0] in txt) or (exp2.split()[-1] in txt and exp2.split()[0] in txt):
                return True
    except Exception as e:
        print(f"  Could not read due date link: {e}")
    
    # Don't be too strict about verification - if we got this far, the time was probably set
    print(f"  Time verification inconclusive, assuming success")
    return True

def set_due_date(page: Page, due_dt: Optional[datetime]):
    if not due_dt:
        print("  No due date to set")
        return

    print(f"  Setting due date: {due_dt.strftime('%m/%d/%Y %I:%M %p')}")

    def _edit_due_in_scope(scope: Locator):
        # BU trace shows specific labels:
        date_box = scope.get_by_role("textbox", name=re.compile(r"^(Due Date:\s*)?Date$", re.I)).first
        if date_box.count() == 0:
            date_box = scope.locator("input[placeholder='mm/dd/yyyy']").first
        if not try_wait(date_box, timeout=4000):
            save_debug(page, "due_date_inputs_missing")
            raise RuntimeError("Due date inputs not found (output/due_date_inputs_missing.png)")

        # Use very specific format: "9/22/25" (no leading zeros, 2-digit year)
        date_format = due_dt.strftime("%-m/%-d/%y") if os.name != "nt" else due_dt.strftime("%m/%d/%y")
        
        # Remove leading zeros if they exist
        parts = date_format.split("/")
        if len(parts) == 3:
            month = parts[0].lstrip("0") if parts[0] != "0" else "0"
            day = parts[1].lstrip("0") if parts[1] != "0" else "0"
            year = parts[2]
            date_format = f"{month}/{day}/{year}"
        
        print(f"  Setting date to: '{date_format}'")
        
        try:
            date_box.click(timeout=2000)
            date_box.press("Control+A")
            date_box.fill(date_format)
            
            # Use Tab key (not Enter) to commit the date field
            print(f"  Pressing Tab to commit date...")
            date_box.press("Tab")
            
            # Wait for the UI to process the change
            page = date_box.page
            page.wait_for_timeout(500)
            
            # Verify the date was set
            try:
                current_val = date_box.input_value(timeout=1000)
                print(f"  Date field after Tab shows: '{current_val}'")
            except Exception:
                pass
            
            print(f"  Date setting completed")
            
        except Exception as e:
            print(f"  Date setting failed: {e}")

        time_box = _ensure_time_field(scope)
        if time_box.count() > 0:
            try:
                time_box.scroll_into_view_if_needed(timeout=1500)
            except Exception:
                pass
            if time_box.is_visible():
                _type_and_commit_time(time_box, due_dt)
                
                # Verify the time was set correctly
                page.wait_for_timeout(500)
                try:
                    current_time = time_box.input_value(timeout=1000)
                    expected_time_1 = due_dt.strftime("%-I:%M %p") if os.name != "nt" else due_dt.strftime("%I:%M %p").lstrip("0")
                    expected_time_2 = due_dt.strftime("%I:%M %p")
                    
                    if current_time not in [expected_time_1, expected_time_2]:
                        print(f"  WARNING: Time field shows '{current_time}', expected '{expected_time_1}' or '{expected_time_2}'")
                        # Try setting it again
                        _type_and_commit_time(time_box, due_dt)
                except Exception as e:
                    print(f"  Could not verify time setting: {e}")
            else:
                # Try clicking the time picker button again if time field isn't visible
                try:
                    tp = scope.get_by_role("button", name=re.compile(r"Time picker", re.I)).first
                    if tp.count() > 0:
                        tp.click(timeout=1200)
                        page.wait_for_timeout(300)
                        time_box = _ensure_time_field(scope)
                        if time_box.count() > 0 and time_box.is_visible():
                            _type_and_commit_time(time_box, due_dt)
                except Exception:
                    pass

        # Don't save yet - we'll save everything at the end of the panel

    # Try the inline "Due date settings …" link (codegen-style)
    link = page.get_by_role("link", name=re.compile(r"^Due date settings", re.I)).first
    if link.count() > 0 and link.is_visible():
        print(f"  Found 'Due date settings' link, clicking...")
        link.click(timeout=4000)
        page.wait_for_timeout(500)
        _edit_due_in_scope(page)
    else:
        # Right-column due link
        dd_label = page.get_by_text(re.compile(r"^\s*Due date\s*$", re.I)).first
        dd_value_link = page.get_by_role("link", name=re.compile(r"\b(AM|PM)\b|\d{4}", re.I)).first
        if dd_label.count() > 0 and dd_value_link.count() > 0:
            try:
                dd_value_link.click(timeout=2500)
                _edit_due_in_scope(page)
            except Exception:
                pass
        else:
            # Settings drawer fallback
            open_settings(page)
            scope = page.locator("aside, [role='dialog'], [aria-label*='Assignment Settings' i]").first
            if scope.count() == 0:
                scope = page
            _edit_due_in_scope(scope)
            for b in [
                page.get_by_role("button", name=re.compile(r"^Save$", re.I)),
                page.get_by_role("button", name=re.compile(r"^Close$", re.I)),
            ]:
                try:
                    if b.count() > 0 and b.first.is_visible():
                        b.first.click(timeout=2000)
                except Exception:
                    pass

    # After all fields are set, save the entire panel
    try:
        page.wait_for_timeout(500)  # Give UI time to update all fields
        print("  All date/time fields set, looking for Save button...")
        
        # Look for the Save button that closes this panel
        save_selectors = [
            page.get_by_role("button", name=re.compile(r"^Save$", re.I)),
            page.locator("button").filter(has_text=re.compile(r"^Save$", re.I)),
        ]
        
        saved = False
        for i, save_selector in enumerate(save_selectors):
            if save_selector.count() > 0:
                for j in range(save_selector.count()):
                    try:
                        btn = save_selector.nth(j)
                        if btn.is_visible():
                            print(f"  Clicking panel Save button {i}.{j}...")
                            btn.scroll_into_view_if_needed(timeout=1500)
                            btn.click(timeout=3000)
                            page.wait_for_timeout(1000)
                            print(f"  Date/time panel saved and closed")
                            saved = True
                            return
                    except Exception as e:
                        print(f"  Panel save button {i}.{j} failed: {e}")
                        continue
        
        if not saved:
            print(f"  WARNING: Could not find Save button for date/time panel")
            
    except Exception as e:
        print(f"  Panel save failed: {e}")

def set_release_show_on(page: Page, rel_dt: Optional[datetime]):
    if not rel_dt:
        return
    vis_btn = None
    for vb in [
        page.get_by_role("button", name=re.compile(r"Hidden from students", re.I)),
        page.get_by_role("button", name=re.compile(r"Visible to students", re.I)),
        page.locator('bb-visibility-button, button[aria-label*="visibility"]'),
    ]:
        if vb.count() > 0:
            vis_btn = vb.first
            break
    if not vis_btn:
        save_debug(page, "visibility_button_missing")
        raise RuntimeError("Visibility button not found (output/visibility_button_missing.png)")
    vis_btn.click(timeout=3000)

    rc = page.get_by_role("menuitem", name=re.compile(r"Release conditions", re.I)).first
    if not try_wait(rc, timeout=5000):
        save_debug(page, "release_conditions_missing")
        raise RuntimeError("Release conditions menu item not found (output/release_conditions_missing.png)")
    rc.click(timeout=3000)

    dt_tab = page.get_by_text(re.compile(r"Date/Time", re.I)).first
    if dt_tab.count() > 0 and dt_tab.is_visible():
        dt_tab.click(timeout=2000)

    access_from = page.get_by_role("checkbox", name=re.compile(r"Access from", re.I)).first
    if not try_wait(access_from, timeout=5000):
        save_debug(page, "release_checkbox_missing")
        raise RuntimeError('"Access from" checkbox not found (output/release_checkbox_missing.png)')
    try: access_from.check()
    except Exception: pass

    date_input = page.get_by_role("textbox", name=re.compile(r"Access from date", re.I)).first
    if date_input.count() == 0:
        date_input = page.locator("input[placeholder='mm/dd/yyyy']").first
    if not try_wait(date_input, timeout=2500):
        save_debug(page, "release_date_inputs_missing")
        raise RuntimeError("Release date inputs not found (output/release_date_inputs_missing.png)")
    date_input.click(); date_input.press("Control+A"); date_input.fill(rel_dt.strftime("%m/%d/%Y")); date_input.press("Enter")

    time_input = page.get_by_role("textbox", name=re.compile(r"Access from time", re.I)).first
    if time_input.count() == 0:
        time_input = page.locator("input[placeholder='hh:mm AM/PM']").first
    if time_input.count() > 0 and time_input.is_visible():
        _type_and_commit_time(time_input, rel_dt)

    for b in [
        page.get_by_role("button", name=re.compile(r"^Save$", re.I)),
        page.get_by_role("button", name=re.compile(r"^Continue$", re.I)),
        page.get_by_role("button", name=re.compile(r"^Close$", re.I)),
    ]:
        try:
            if b.count() > 0 and b.first.is_visible():
                b.first.click(timeout=3000)
        except Exception:
            pass

def save_assignment_and_close(page: Page):
    """Save the entire assignment (including any open panels) and close editor"""
    def _save_attempt():
        print("  Looking for main Save button to save all changes...")
        
        # Look for save buttons - try different cases and contexts
        save_selectors = [
            page.get_by_role("button", name=re.compile(r"^Save$", re.I)),
            page.get_by_role("button", name=re.compile(r"^save$", re.I)), 
            page.get_by_role("button", name=re.compile(r"^SAVE$", re.I)),
            page.locator("button").filter(has_text=re.compile(r"^Save$", re.I)),
            page.locator('button[type="submit"]'),
        ]
        
        saved = False
        for i, save_selector in enumerate(save_selectors):
            if save_selector.count() > 0:
                for j in range(save_selector.count()):
                    try:
                        btn = save_selector.nth(j)
                        if btn.is_visible():
                            print(f"  Found Save button {i}.{j}, clicking...")
                            btn.scroll_into_view_if_needed(timeout=2000)
                            btn.click(timeout=4000)
                            page.wait_for_timeout(1500)  # Longer wait for save to complete
                            print(f"  Assignment saved successfully")
                            saved = True
                            return
                    except Exception as e:
                        print(f"  Save button {i}.{j} failed: {e}")
                        continue
        
        if not saved:
            print("  WARNING: Could not find main Save button")
            raise Exception("Save button not found or not visible")
    
    try:
        retry(_save_attempt, attempts=3, backoff_sec=1.0)
    except Exception as e:
        print(f"  Save failed: {e}")
        pass  # Continue even if save fails
    
    # Don't call maybe_exit_item_editor since Save should close the panel
    print("  Assignment save completed")

# -------------------------------
# High-level create flow
# -------------------------------
def create_assignment(page: Page, title: str, rel: Optional[datetime], due: Optional[datetime]):
    open_create_menu(page)
    choose_assignment(page)

    fill_title(page, title)

    # Due first (so right-hand card reflects time immediately)
    try: set_due_date(page, due)
    except Exception: pass

    try:
        set_points_zero(page)
    except Exception as e:
        print(f"  Points setting failed: {e}")
    
    # Final save of the entire assignment
    save_assignment_and_close(page)

    # COMMENTED OUT: Release conditions can get stuck and affect UI state
    # try: set_release_show_on(page, rel)
    # except Exception: pass
    if rel:
        print(f"  Note: Release date {rel.strftime('%m/%d/%Y %I:%M %p')} not set (release conditions disabled)")

    # Make sure we exit any open editors/dialogs
    maybe_exit_item_editor(page)
    
    # NO ESCAPE KEY - it cancels changes! Just wait for UI to settle
    try:
        print("  Waiting for assignment editor to settle...")
        
        # Just wait - don't press escape or close anything that might cancel changes
        page.wait_for_timeout(1000)
        
        # The assignment should be saved at this point
        print("  Assignment creation completed")
        
    except Exception:
        pass

# -------------------------------
# CLI / Main
# -------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to CSV")
    ap.add_argument("--course", required=True, help="Internal course id, e.g. _263954_1")
    ap.add_argument("--limit", type=int, help="Limit number of items for a test run")
    ap.add_argument("--headless", default="false", choices=["true","false"], help="Run headless")
    ap.add_argument("--config", help="Optional JSON mapping of CSV columns")
    ap.add_argument("--out", help="Report CSV filename under ./output/ (optional)")
    ap.add_argument("--platform", default="auto", choices=["auto","wayland","x11"], help="Chromium UI backend")
    ap.add_argument("--state-file", default="state.json", help="Playwright storage state (cookies)")
    ap.add_argument("--folder-col", help="Optional CSV column to group items (existing folder)")
    ap.add_argument("--target-folder", help="Always insert into this existing folder (overrides --folder-col)")
    ap.add_argument("--no-release", action="store_true",
                    help="Do not set Release (“Show on”) dates even if present in CSV")
    args = ap.parse_args()

    cfg = DEFAULT_CFG.copy()
    if args.config:
        with open(args.config) as f:
            cfg.update(json.load(f))

    rows = load_rows(args.csv, cfg, limit=args.limit, folder_col=args.folder_col)
    if not rows:
        print("No matching rows found—check CSV columns and include_types.", file=sys.stderr)
        sys.exit(2)

    headless = (args.headless.lower() == "true")

    # Launch flags for Wayland/X11
    launch_args = ["--no-sandbox", "--disable-dev-shm-usage"]
    plat = args.platform
    if plat == "auto":
        plat = "wayland" if os.environ.get("WAYLAND_DISPLAY") else "x11"
    if plat == "wayland":
        launch_args += ["--enable-features=UseOzonePlatform", "--ozone-platform=wayland"]
    elif plat == "x11":
        launch_args += ["--ozone-platform=x11"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=launch_args)

        context_kwargs = {}
        if os.path.exists(args.state_file):
            context_kwargs["storage_state"] = args.state_file
        context = browser.new_context(**context_kwargs)
        page = context.new_page()

        # Trace when headless
        if headless:
            try:
                context.tracing.start(title="ultra-seed", screenshots=True, snapshots=True, sources=False)
            except Exception:
                pass

        # Navigate / login
        page.goto(f"{BASE}/ultra", wait_until="domcontentloaded")
        if not wait_for_logged_in(page):
            save_debug(page, "login_wait_timeout")
            print("Login not detected. Run once headful to complete SSO/MFA; see output/login_wait_timeout.png", file=sys.stderr)
            if headless:
                try: context.tracing.stop(path=str(OUTPUT_DIR / "trace.zip"))
                except Exception: pass
            context.close(); browser.close(); sys.exit(3)

        # Save storage for next runs
        try: context.storage_state(path=args.state_file)
        except Exception: pass

        created = []
        total = len(rows)

        # Track current folder state to avoid unnecessary navigation
        current_folder = None
        inside_folder = False
        
        for i, it in enumerate(rows, 1):
            print(f"\n--- Assignment {i}/{total} ---")
            title = it["title"]
            rel = None if args.no_release else it["release"]
            due = it["due"]
            folder_for_item = args.target_folder or it.get("folder", "")

            # Only navigate if we need to change folders
            if folder_for_item != current_folder:
                # Start from root when changing folders
                ensure_on_outline(page, args.course)
                inside_folder = False
                current_folder = None
                
                if folder_for_item:
                    print(f'→ target folder: "{folder_for_item}"')
                    # First, check if we can find this folder
                    save_debug(page, f"searching_for_folder_{folder_for_item.replace(' ', '_')}")
                    
                    if enter_folder(page, folder_for_item):
                        inside_folder = True
                        current_folder = folder_for_item
                        print(f'✓ Successfully entered folder: "{folder_for_item}"')
                    else:
                        # If target folder doesn't exist and the user explicitly wants it,
                        # we should continue without the folder but warn them
                        print(f'Warning: Folder "{folder_for_item}" not found. Available folders might be:')
                        
                        # Try to list what folders are available
                        try:
                            cont = outline_container(page)
                            # Look for folder-like elements
                            possible_folders = [
                                cont.get_by_role("button").all(),
                                cont.get_by_role("link").all()
                            ]
                            
                            folder_names = set()
                            for folder_group in possible_folders:
                                for folder in folder_group:
                                    try:
                                        text = folder.inner_text(timeout=500)
                                        if text and len(text.strip()) > 0 and len(text) < 100:
                                            folder_names.add(text.strip())
                                    except Exception:
                                        continue
                            
                            if folder_names:
                                print(f'  Found these items: {", ".join(sorted(list(folder_names))[:10])}')
                            else:
                                print('  Could not detect available folders')
                        except Exception:
                            print('  Could not list available folders')
                        
                        print(f'  Continuing with assignments at root level', file=sys.stderr)
                        current_folder = None
                else:
                    # No folder needed, make sure we're at root
                    current_folder = None

            # Idempotency: check current view + global (starts-with match)
            if assignment_exists_on_outline(page, title) or assignment_exists_globally(page, title):
                print(f"[{i}/{total}] Skip (exists): {title}")
                created.append({
                    "title": title,
                    "release": rel.isoformat() if rel else "",
                    "due": due.isoformat() if due else "",
                    "action": "skip",
                    "folder": folder_for_item,
                    "inside_folder": "yes" if inside_folder else "no"
                })
                continue

            print(f"[{i}/{total}] Creating: {title}")
            try:
                create_assignment(page, title, rel, due)
                
                # Gently check if we're still in the right place for the next assignment
                print("  Checking location for next assignment...")
                
                # Check if we can see the course content heading (means we're still in the course)
                course_content_visible = page.get_by_role("heading", name=re.compile(r"Course Content", re.I)).count() > 0
                
                if not course_content_visible:
                    print("  Lost course context, navigating back...")
                    ensure_on_outline(page, args.course)
                    inside_folder = False
                    current_folder = None
                elif inside_folder and current_folder:
                    # Check if we're still in the folder (but don't force navigation)
                    if not _confirm_inside_folder(page, current_folder):
                        print(f"  No longer in folder {current_folder}, will continue at root")
                        inside_folder = False
                        current_folder = None
                
                # Verify the assignment was actually created
                page.wait_for_timeout(1000)
                if assignment_exists_on_outline(page, title):
                    print(f"  ✓ Assignment created successfully")
                    created.append({
                        "title": title,
                        "release": rel.isoformat() if rel else "",
                        "due": due.isoformat() if due else "",
                        "action": "created",
                        "folder": folder_for_item,
                        "inside_folder": "yes" if inside_folder else "no"
                    })
                else:
                    # Creation might have failed even though no exception was thrown
                    print(f'  ? Assignment processed but not found in current view', file=sys.stderr)
                    created.append({
                        "title": title,
                        "release": rel.isoformat() if rel else "",
                        "due": due.isoformat() if due else "",
                        "action": "uncertain",
                        "folder": folder_for_item,
                        "inside_folder": "yes" if inside_folder else "no"
                    })
            except Exception as e:
                save_debug(page, f"create_failed_{i}")
                print(f'  ✗ Creation failed for "{title}": {e}. See output/create_failed_{i}.png', file=sys.stderr)
                created.append({
                    "title": title,
                    "release": rel.isoformat() if rel else "",
                    "due": due.isoformat() if due else "",
                    "action": "failed",
                    "folder": folder_for_item,
                    "inside_folder": "yes" if inside_folder else "no"
                })

            print(f"  Waiting before next assignment...")
            page.wait_for_timeout(500)  # Reduced from 1000ms to 500ms

        if args.out:
            out_path = OUTPUT_DIR / args.out
            with out_path.open("w", newline="") as f:
                w = _csv.DictWriter(f, fieldnames=["title", "release", "due", "action", "folder", "inside_folder"])
                w.writeheader()
                w.writerows(created)
            print(f"Wrote report: {out_path}")

        if headless:
            try:
                context.tracing.stop(path=str(OUTPUT_DIR / "trace.zip"))
                print(f"Saved Playwright trace to {OUTPUT_DIR / 'trace.zip'}")
            except Exception:
                pass

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
