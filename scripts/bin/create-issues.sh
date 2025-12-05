#!/bin/bash
# Script to create GitHub issues from todos.txt
# Usage: ./create-issues.sh

set -e

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed or not in PATH"
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Get current branch for issue prefix
BRANCH=$(git branch --show-current)
if [ -z "$BRANCH" ]; then
    echo "Error: Could not determine current branch"
    exit 1
fi

# Check if todos.txt exists
if [ ! -f "todos.txt" ]; then
    echo "Error: todos.txt not found in current directory"
    exit 1
fi

echo "Creating GitHub issues from todos.txt..."
echo "Branch: $BRANCH"
echo "Repository: $(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo 'unknown')"
echo ""

ISSUE_COUNT=0

# Read todos.txt and create issues for TODO items
while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue

    # Check if line starts with TODO number
    if [[ $line =~ ^[0-9]+\. ]]; then
        # Extract the todo number and description
        TODO_NUM=$(echo "$line" | sed 's/^\([0-9]\+\)\..*/\1/')
        TODO_DESC=$(echo "$line" | sed 's/^[0-9]\+\. //')

        # Skip if description is empty
        [ -z "$TODO_DESC" ] && continue

        # Create issue title with branch prefix
        ISSUE_TITLE="[${BRANCH}] TODO ${TODO_NUM}: ${TODO_DESC}"

        # Create issue body with context
        ISSUE_BODY="**Original TODO from todos.txt:**
${TODO_DESC}

**Context:**
- Branch: ${BRANCH}
- File: todos.txt
- TODO Number: ${TODO_NUM}

**Status:** Open - needs implementation

*This issue was automatically created from the project todos list.*"

        echo "Creating issue: ${ISSUE_TITLE}"

        # Create the GitHub issue
        if gh issue create --title "${ISSUE_TITLE}" --body "${ISSUE_BODY}"; then
            echo "✓ Created issue for TODO ${TODO_NUM}"
            ISSUE_COUNT=$((ISSUE_COUNT + 1))
        else
            echo "✗ Failed to create issue for TODO ${TODO_NUM}"
        fi

        echo ""
    fi
done < todos.txt

echo "Issue creation complete!"
echo "Created ${ISSUE_COUNT} issues from todos.txt"
echo ""
echo "View issues: gh issue list"
echo "Or visit: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/issues"