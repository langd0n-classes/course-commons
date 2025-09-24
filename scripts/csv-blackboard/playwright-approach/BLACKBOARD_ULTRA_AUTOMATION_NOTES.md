# Blackboard Ultra UI Automation - Lessons Learned

## Overview
This document captures key insights, patterns, and gotchas discovered while building a Playwright-based automation script for creating assignments in Blackboard Ultra (BU tenant: learn.bu.edu).

## Key UI Patterns & Selectors

### Course Outline Container
**Problem**: The expected selector `[data-automation-id="course-outline"]` often doesn't exist.
**Solution**: Use fallback hierarchy:
```python
def outline_container(page: Page) -> Locator:
    # Try specific selector first
    specific = page.locator('[data-automation-id="course-outline"]')
    if specific.count() > 0:
        return specific
    
    # Fallback options
    fallbacks = [
        page.locator('.course-outline-content-list'),
        page.locator('[class*="course-outline"]'),
        page.locator('[class*="content-list"]'),
        page.locator('main'),
        page,  # Ultimate fallback
    ]
```

### Folder Detection & Navigation

#### Folder States
- **Closed folder**: `aria-expanded="false"`, no `folder-contents-[ID]` element visible
- **Open folder**: `aria-expanded="true"`, `folder-contents-[ID]` element visible

#### Key Selectors for Folders
```python
# Folder toggle buttons
'button[data-analytics-id="content.item.folder.toggleFolder.button"]'
'button[aria-expanded]'
'button[id*="folder-title"]'

# Folder content area (definitive indicator you're INSIDE a folder)
'[id^="folder-contents-"]'
```

#### Critical Insight: Folder Detection
**Wrong approach**: Detecting folder by heading text (just means folder exists)
**Right approach**: Detecting folder content area (means you're actually inside it)

```python
def _confirm_inside_folder(page: Page, name: str) -> bool:
    # The folder content area is the DEFINITIVE indicator
    folder_content_area = page.locator('[id^="folder-contents-"]')
    return folder_content_area.count() > 0
```

### Plus Button Detection (Add Content)

#### Context Matters
- **Root level**: Generic plus buttons work
- **Inside folders**: Must use folder-specific plus buttons

#### Folder-Specific Plus Button Patterns
When inside a folder, look within the folder content area:
```python
folder_content_area = page.locator('[id^="folder-contents-"]')
folder_plus_selectors = [
    folder_content_area.get_by_role("button", name=re.compile(r"Add new content below", re.I)),
    folder_content_area.get_by_role("button", name=re.compile(r"Add new content above", re.I)),
    folder_content_area.get_by_role("button", name=re.compile(r"^Add new content$", re.I)),
    folder_content_area.locator('button[aria-label*="Add new content"]'),
    folder_content_area.locator('button.makeStylesaddButton-0-2-594'),
    folder_content_area.locator('button[id^="add-content-menu-button"]'),
]
```

#### Plus Button Revelation Strategy
Plus buttons appear on hover. For folders:
1. Hover over folder content area
2. Hover over last content item in folder
3. Hover at bottom of folder content area

### Assignment Creation Flow

#### Date/Time Setting
**Critical**: Use `Tab` key, not `Enter` to commit form fields:
```python
# Correct approach
date_box.fill(date_format)
date_box.press("Tab")  # NOT Enter!

time_box.fill(time_format)  
time_box.press("Tab")  # NOT Enter!
```

#### Points Setting
Look for grading links in right column:
```python
grading_patterns = [
    re.compile(r"Grading.*maximum points", re.I),
    re.compile(r"\d+\s+maximum points", re.I),
    re.compile(r"maximum points", re.I),
]
```

## Timing & Performance

### Page Load Considerations
- **Problem**: Content loads dynamically, folders may not be immediately available
- **Solution**: Quick readiness check, don't over-wait:
```python
try:
    page.wait_for_selector('button, [class*="content"]', timeout=3000)
except Exception:
    pass  # Continue anyway
```

### Optimal Timeout Values
Based on testing, these values provide good balance of reliability vs speed:
```python
try_wait(locator, timeout=1500)  # Default wait
elem.click(timeout=1200)         # Click actions  
elem.scroll_into_view_if_needed(timeout=800)  # Scrolling
page.wait_for_timeout(300)       # Brief pauses
page.wait_for_timeout(500)       # Between assignments
```

### Performance Optimizations
- Reduced folder expand wait: 1000ms → 300ms
- Reduced hover waits: 800ms → 500ms, 400ms → 200ms  
- Reduced inter-assignment delay: 1000ms → 500ms
- **Total savings**: ~4-5 seconds per assignment

## Critical Gotchas

### 1. Folder Context Loss
**Problem**: After creating assignment, may lose folder context
**Solution**: Re-verify folder state before next assignment

### 2. Assignment Editor State
**Problem**: Assignment creation can leave editor panels open
**Solution**: Always call `maybe_exit_item_editor()` and wait for UI to settle

### 3. Idempotency Detection
**Pattern**: Use both starts-with and exact match patterns:
```python
def assignment_exists_in_scope(scope: Locator, title: str) -> bool:
    pat = _starts_with(title)
    exact_pat = re.compile(rf"^\s*{re.escape(title)}\s*$", re.I)
    
    # Check both patterns across multiple element types
    for c in [
        scope.get_by_role("link", name=pat),
        scope.get_by_role("heading", name=pat),
        scope.get_by_role("link", name=exact_pat),
        scope.get_by_role("heading", name=exact_pat),
    ]:
        # Check for visible matches...
```

### 4. HTML Structure Variations
**Problem**: Blackboard Ultra uses dynamically generated CSS class names
**Solution**: Rely on semantic attributes when possible:
- `data-analytics-id` attributes
- `aria-*` attributes  
- `id` patterns rather than specific class names

## Debugging Strategies

### Screenshots for Debugging
Always save debug screenshots at key points:
```python
def save_debug(page: Page, name: str):
    try:
        page.screenshot(path=str(OUTPUT_DIR / f"{name}.png"), full_page=True)
    except Exception:
        pass
```

### Logging Patterns
Use descriptive logging to track state:
```python
print(f"  ✓ Confirmed inside folder '{name}' (heading: {h.count()}, content-area: {folder_content_area.count()})")
print(f"  Found folder plus button {i}.{j}, clicking...")
print(f"  Folder aria-expanded: {expanded_attr}")
```

## Best Practices

### 1. Robust Element Detection
Always check element visibility and provide fallbacks:
```python
if elem.is_visible():
    elem.scroll_into_view_if_needed(timeout=800)
    elem.click(timeout=1200)
```

### 2. State Verification
Verify critical state changes:
```python
# After clicking folder toggle
if _confirm_inside_folder(page, name):
    return True
```

### 3. Error Handling
Use retry logic for flaky operations:
```python
def retry(fn, attempts=2, backoff_sec=0.8):
    last = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            time.sleep(backoff_sec)
    raise last
```

## Future Automation Considerations

### 1. Selector Stability
- Prefer `data-*` attributes over CSS classes
- Use semantic roles (`button`, `link`, `heading`) when possible
- Have multiple selector strategies as fallbacks

### 2. Content Loading
- Blackboard Ultra loads content dynamically
- Always verify elements exist before interacting
- Use reasonable timeouts, not excessive waits

### 3. UI State Management
- Track current folder context between operations
- Always clean up editor states
- Verify expected state before proceeding with next operation

### 4. Scale Considerations
- For large batches, optimize timeouts
- Consider using `--headless` mode for production runs
- Implement proper error recovery and reporting

## Example CSV Processing
For date/time modifications, simple CSV processing works well:
```python
import csv
import re

# Pattern to match and replace times
pattern = r'(\d{2}/\d{2}/\d{2})\s+10:00\s+AM'
replacement = r'\1 02:30 PM'
modified_date = re.sub(pattern, replacement, original_date, flags=re.IGNORECASE)
```

## Environment Setup
For devcontainers, ensure Python dependencies:
```dockerfile
RUN apt install -y \
  python3 \
  python3-pip \
  python3-pandas \
  python3-dateutil
```

---

**Created**: December 2024  
**Context**: Blackboard Ultra assignment automation with Playwright  
**Success Rate**: High reliability achieved with proper folder detection and context management