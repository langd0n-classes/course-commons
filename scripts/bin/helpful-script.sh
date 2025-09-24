#!/bin/bash

# you have to copy this in to every place you use it in a notebook
# because otter-grader assign can't follow symlinks

# Function to display usage information
display_usage() {
    echo "Usage: ./helpful_script.sh <operation>"
    echo "Valid operations are 'setup' and 'save'."
    exit 1
}

# Function for 'setup' operation
setup() {
    echo "Running setup..."
    pip install otter-grader numpy matplotlib datascience
    save
}

# Function for 'save' operation
save() {
    echo "Running save..."
    git add .
    git commit -m "saving commit: $(date '+%m/%d/%Y %H:%M')"
    git push
}

# Check if the script received an argument
if [ "$#" -ne 1 ] || [ "$1" == "--help" ] || [ "$1" != "setup" ] && [ "$1" != "save" ]; then
    display_usage
fi

# Get the git repo root directory
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
