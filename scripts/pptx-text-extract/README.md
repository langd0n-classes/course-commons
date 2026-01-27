# PPTX Text Extractor

Extract text from PPTX files into .txt sidecar files for easy parsing by GenAI tools.

## Requirements

- Python 3.10+
- Install deps:

```
pip install -r requirements.txt
```

## Usage

```
python extract_pptx_text.py
```

By default, it processes `*.pptx` in the current directory and writes `.txt` files next to each PPTX.

### Examples

```
# Process a single file
python extract_pptx_text.py slides.pptx

# Process a directory of slides
python extract_pptx_text.py ./slides/*.pptx

# Write outputs to a separate directory
python extract_pptx_text.py ./slides/*.pptx --out-dir ./texts

# Overwrite existing .txt outputs
python extract_pptx_text.py ./slides/*.pptx --overwrite

# Include slide layout/title (notes included by default)
python extract_pptx_text.py ./slides/*.pptx --include-layout

# Skip speaker notes
python extract_pptx_text.py ./slides/*.pptx --no-notes

# Write JSON output instead of plain text
python extract_pptx_text.py ./slides/*.pptx --json --out-dir ./json
```

## Notes

- If a slide contains no text boxes, it will still get a slide header.
- Speaker notes are included by default; use `--no-notes` to skip them.
- Use `--include-layout` to add layout and title metadata.
- Use `--json` for structured outputs per slide.
