#!/usr/bin/env python3
"""
Convert markdown outline with solutions to Jupyter Notebook with Otter Grader DSL.

Input format: Markdown file with questions separated by '---' markers.
Each question has:
- ### Question X.Y: Title
- points: N
- manual: true/false
- Question text/prompt
- >>> SOLUTION (for code or text answers)
- >>> TESTS (for autograded questions)

Output: Properly formatted Jupyter notebook with Otter DSL.
"""

import nbformat
import argparse
import re
import os

# --- Default Templates and Boilerplate ---

ASSIGNMENT_CONFIG = """# ASSIGNMENT CONFIG
init_cell: true
export_cell: false
files:
    - d8error.py
    - errorConfig.json
    - helpful-script.sh
solutions_pdf: false
template_pdf: false
requirements:
    - pandas
    - numpy
generate:
    show_stdout: true
    filtering: true
    pagebreaks: true
    zips: false"""

SETUP_SCRIPT_CELL = """%%capture
%%sh
chmod u+x ./helpful-script.sh
./helpful-script.sh setup"""

SAVE_CHECKPOINT_CELL = "!./helpful-script.sh save 1>/dev/null"


def parse_question_metadata(lines):
    """Extract question metadata (points, manual flag)."""
    metadata = {'points': 10, 'manual': False}

    for line in lines:
        line = line.strip()
        if line.startswith('points:'):
            metadata['points'] = int(line.split(':', 1)[1].strip())
        elif line.startswith('manual:'):
            metadata['manual'] = line.split(':', 1)[1].strip().lower() == 'true'

    return metadata


def extract_solution_and_tests(section):
    """Extract solution code and test blocks from a question section."""
    solution = None
    tests = []

    # Find solution block
    solution_match = re.search(r'>>> SOLUTION\n(.*?)(?=>>> TESTS|---|\Z)', section, re.DOTALL)
    if solution_match:
        solution = solution_match.group(1).strip()

    # Find tests block
    tests_match = re.search(r'>>> TESTS\n(.*?)(?=---|\Z)', section, re.DOTALL)
    if tests_match:
        test_block = tests_match.group(1).strip()
        # Split tests by blank lines (each test is separate)
        tests = [t.strip() for t in re.split(r'\n\s*\n', test_block) if t.strip()]

    return solution, tests


def is_text_answer(solution):
    """Determine if solution is a text answer (vs code function)."""
    if not solution:
        return False
    # Text answers are variable assignments with triple-quoted strings
    return solution.strip().startswith(('q', 'reflection =')) and '"""' in solution


def create_text_answer_prompt(question_text):
    """Generate appropriate prompt for text answer based on question requirements."""
    # Extract key requirements from question text
    if 'table' in question_text.lower():
        return '"""YOUR TABLE HERE (markdown format)"""'
    elif '4-5 sentences' in question_text:
        return '"""YOUR ANSWER HERE (4-5 sentences)"""'
    elif '4-6 sentences' in question_text:
        return '"""YOUR ANSWER HERE (4-6 sentences)"""'
    elif '3-4 sentences' in question_text:
        return '"""YOUR ANSWER HERE (3-4 sentences)"""'
    elif '2-3 sentences' in question_text or 'methodology note' in question_text.lower():
        return '"""YOUR METHODOLOGY NOTE HERE (2-3 sentences)"""'
    elif '150-200 word' in question_text:
        return '"""YOUR SUMMARY HERE (150-200 words)"""'
    elif '200-250 word' in question_text:
        return '"""YOUR REFLECTION HERE (200-250 words)"""'
    elif 'checklist' in question_text.lower():
        return '"""YOUR CHECKLIST HERE"""'
    elif '5-7' in question_text or 'edge case' in question_text.lower():
        return '"""YOUR EDGE CASES LIST HERE (5-7 cases)"""'
    elif '4-6 bullet points' in question_text or 'pipeline' in question_text.lower():
        return '"""YOUR PIPELINE SKETCH HERE (4-6 bullet points)"""'
    elif 'framework' in question_text.lower() or 'flowchart' in question_text.lower():
        return '"""YOUR DECISION FRAMEWORK HERE (table or flowchart)"""'
    elif 'document' in question_text.lower() or 'describe' in question_text.lower():
        return '"""YOUR DOCUMENTATION HERE"""'
    else:
        return '"""YOUR ANSWER HERE"""'


def create_text_completion_tests(var_name):
    """Create completion tests for text answer variables."""
    return [
        f"# Test that answer exists and is not empty\nassert isinstance({var_name}, str) and len({var_name}.strip()) > 0",
        f"# Test that answer has reasonable length (at least 50 characters)\nassert len({var_name}.strip()) >= 50"
    ]


def create_notebook_from_markdown(md_path, ipynb_path):
    """
    Parse markdown file and generate Jupyter Notebook with Otter Grader DSL.
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    nb = nbformat.v4.new_notebook()

    # Add metadata
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.9.0"
        }
    }

    # Add boilerplate
    nb.cells.append(nbformat.v4.new_raw_cell(ASSIGNMENT_CONFIG))
    nb.cells.append(nbformat.v4.new_code_cell(SETUP_SCRIPT_CELL))

    # Split content by '---' separators
    sections = re.split(r'\n---\n', md_content)

    # First section is the header/intro
    if sections:
        header_content = sections[0].strip()
        nb.cells.append(nbformat.v4.new_markdown_cell(header_content))

    # Process each question section
    for section in sections[1:]:
        section = section.strip()
        if not section:
            continue

        # Check if this is a question or just markdown
        question_match = re.match(r'### Question (\d+\.\d+): (.+)', section)

        if not question_match:
            # Not a question, just add as markdown
            nb.cells.append(nbformat.v4.new_markdown_cell(section))
            continue

        # Parse question
        q_num = question_match.group(1)
        q_title = question_match.group(2).strip()
        q_part, q_sub = q_num.split('.')

        # Create question name slug
        q_name_slug = re.sub(r'[^a-z0-9_]', '', q_title.lower().replace(' ', '_'))
        q_name = f"q{q_part}_{q_sub}_{q_name_slug}"

        # Extract metadata
        lines = section.split('\n')
        metadata = parse_question_metadata(lines)

        # Extract question text (everything before >>> SOLUTION)
        question_text = re.split(r'>>> SOLUTION', section)[0].strip()
        # Remove the first line (question header) and metadata lines
        question_lines = []
        skip_metadata = False
        for line in question_text.split('\n')[1:]:  # Skip header line
            if line.strip().startswith(('points:', 'manual:')):
                skip_metadata = True
                continue
            if skip_metadata and line.strip() and not line.strip().startswith(('points:', 'manual:')):
                skip_metadata = False
            if not skip_metadata:
                question_lines.append(line)
        question_prompt = '\n'.join(question_lines).strip()

        # Extract solution and tests
        solution, tests = extract_solution_and_tests(section)

        # Determine if this is autograded
        is_manual = metadata['manual']

        # Create cells for this question
        # 1. BEGIN QUESTION marker
        nb.cells.append(nbformat.v4.new_raw_cell(
            f"# BEGIN QUESTION\nname: {q_name}\npoints: {metadata['points']}\nmanual: {str(is_manual).lower()}"
        ))

        # 2. Question text
        nb.cells.append(nbformat.v4.new_markdown_cell(
            f"### Question {q_num}: {q_title}\n\n{question_prompt}"
        ))

        # 3. Solution cell
        if solution:
            is_text = is_text_answer(solution)

            if is_text:
                # Text answer: variable assignment with BEGIN/END SOLUTION
                var_name = solution.split('=')[0].strip()
                prompt = create_text_answer_prompt(question_prompt)

                solution_cell = f"{var_name} = {prompt}\n# BEGIN SOLUTION\n{solution}\n# END SOLUTION"
                nb.cells.append(nbformat.v4.new_code_cell(solution_cell))

                # Add completion tests for text answers if autograded
                if not is_manual and not tests:
                    tests = create_text_completion_tests(var_name)
            else:
                # Code answer: function with # SOLUTION marker
                nb.cells.append(nbformat.v4.new_code_cell(solution))

        # 4. Tests (if autograded and tests exist)
        if not is_manual and tests:
            nb.cells.append(nbformat.v4.new_raw_cell("# BEGIN TESTS"))

            # Add each test as separate code cell
            for test in tests:
                nb.cells.append(nbformat.v4.new_code_cell(test))

            nb.cells.append(nbformat.v4.new_raw_cell("# END TESTS"))

        # 5. END QUESTION marker
        nb.cells.append(nbformat.v4.new_raw_cell("# END QUESTION"))

        # 6. Save checkpoint
        nb.cells.append(nbformat.v4.new_code_cell(SAVE_CHECKPOINT_CELL))

    # Write notebook
    with open(ipynb_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

    print(f"✓ Successfully created notebook: {ipynb_path}")
    print(f"  {len([c for c in nb.cells if 'BEGIN QUESTION' in str(c.get('source', ''))])} questions")
    print(f"  {len(nb.cells)} total cells")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert markdown with solutions to Jupyter Notebook with Otter Grader DSL."
    )
    parser.add_argument(
        "markdown_file",
        help="Path to input markdown file (e.g., gaie-07-text-analysis-source.md)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path for output .ipynb file (defaults to same name as input)"
    )

    args = parser.parse_args()

    output_path = args.output
    if not output_path:
        base_name = os.path.splitext(args.markdown_file)[0]
        output_path = base_name + ".ipynb"

    create_notebook_from_markdown(args.markdown_file, output_path)
