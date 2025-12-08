#!/bin/bash

# you have to copy this in to every place you use it in a notebook
# because otter-grader assign can't follow symlinks

# Function to display usage information
display_usage() {
    echo "Usage: ./helpful_script.sh <operation>"
    echo "Valid operations are 'setup' and 'save'."
    exit 1
}

# Helper to run git commands quietly unless they fail
#
# Usage:
#   run_git_quiet "human-readable description" git subcommand args...
#
# Example:
#   run_git_quiet "add" add .
#
# Behavior:
#   - On success: git's stderr output is discarded.
#   - On failure: the captured stderr is printed, and we return the git exit code.
run_git_quiet() {
    local desc="$1"
    shift

    # Temporary file to capture stderr
    local err_file
    err_file="$(mktemp)"

    # Run the git command, capturing stderr
    if git "$@" 2>"$err_file"; then
        # Success: discard captured output
        rm -f "$err_file"
    else
        # Failure: show captured output and propagate the error
        echo "Error during git ${desc}:" >&2
        cat "$err_file" >&2
        rm -f "$err_file"
        return 1
    fi
}

# Function for 'setup' operation
setup() {
    echo "Running setup..."
    pip install pandas numpy sqlalchemy requests beautifulsoup4 pyspark matplotlib otter-grader
    save
}

# Function for 'save' operation
save() {
    echo "Running save..."

    # Add all changes
    run_git_quiet "add" add . || return 1

    # Commit changes
    run_git_quiet "commit" commit -m "saving commit: $(date '+%m/%d/%Y %H:%M')" || return 1

    # Push changes
    run_git_quiet "push" push || return 1
}

# Check if the script received an argument
if [ "$#" -ne 1 ] || [ "$1" == "--help" ] || { [ "$1" != "setup" ] && [ "$1" != "save" ]; }; then
    display_usage
fi

# Get the git repo root directory
# (stderr already sent to /dev/null here so students won't see this check)
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [ $? -eq 0 ] && [ -f "$REPO_ROOT/.instructor" ]; then
    echo "Detected instructor environment - skipping execution"
    exit 0
else
    echo "Running student version"
    # Your main script logic here
fi

# Get the operation argument
operation=$1

# Check for valid operation and call corresponding function
if [ "$operation" == "setup" ]; then
    setup
elif [ "$operation" == "save" ]; then
    save
fi
