# Incomplete Form Generator

This script creates a PDF version of the BU incomplete grade form using LaTeX and (optionally) a logo image.

## Dependencies (Fedora 43+)

System packages:

```
sudo dnf install texlive-scheme-basic texlive-collection-latex imagemagick
```

Notes:
- `pdflatex` comes from TeX Live (the packages above cover what this script uses).
- `convert` comes from ImageMagick and is only needed if your logo is a GIF.
- The script itself has no third-party Python package dependencies.

## Usage

```
python generate_incomplete_form.py
```

You can also run non-interactively with flags (see `--help`).
