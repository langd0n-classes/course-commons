# Google Drive Slide Export Bundles

Export Google Slides decks from Google Drive into a labeled local bundle.

This tool is intentionally generic. It downloads raw exports and writes metadata,
but it does not rename files to course-specific conventions or place them in a
course repo.

## What it does

- Export one Google Slides deck or all direct-child decks in a Drive folder
- Export each deck as:
  - PDF
  - plain text
- Write a `metadata.json` file describing the run and every exported file
- Stop there

## Requirements

- Python 3.11+
- `GOOGLE_APPLICATION_CREDENTIALS` pointing to a readable service-account JSON key
- The service account must have at least Viewer access to the Shared Drive or folder
- The Google Drive API must be enabled for the Google Cloud project tied to the service account

Install deps:

```bash
pip install -r requirements.txt
```

## Container usage

This directory includes a self-contained `Containerfile` and `Makefile`, so the
tool does not depend on some unrelated prebuilt image.

Build:

```bash
make podman-build
```

Run:

```bash
make podman-run \
  KEY_FILE=/path/to/service-account.json \
  ARGS="--label ds551-202601-S26 --file https://docs.google.com/presentation/d/<deck-id>/edit"
```

The run target mounts the service-account key read-only and writes the output
bundle to `./output` by default. Override with `OUTPUT_DIR=/path/to/output`.

## Usage

### Help

```bash
python export_bundles.py --help
```

### Interactive mode

If you provide no `--file` or `--folder`, the tool prompts for the missing values.

```bash
python export_bundles.py
```

### Export one deck

```bash
python export_bundles.py \
  --label ds551-202601-S26 \
  --file 'https://docs.google.com/presentation/d/<deck-id>/edit'
```

### Export all decks in a folder

```bash
python export_bundles.py \
  --label ds551-202601-S26 \
  --folder 'https://drive.google.com/drive/folders/<folder-id>'
```

### Choose an explicit output directory

```bash
python export_bundles.py \
  --label ds551-202601-S26 \
  --folder '<folder-id>' \
  --output-dir /tmp/ds551-export-bundle
```

If `--output-dir` is omitted, the tool creates a timestamped bundle under the
system temp root.

## Output shape

The output directory contains:

- one `.pdf` and one `.txt` per exported presentation, using the original Drive title
- `metadata.json`

`metadata.json` includes:

- label
- download timestamp
- source mode (`file` or `folder`)
- original source input
- resolved file/folder ID
- file count
- per-file metadata:
  - Drive file ID
  - title
  - Drive MIME type
  - webViewLink
  - created/modified timestamps
  - exported filenames, MIME types, and byte counts

## Notes

- Folder mode exports only direct-child Google Slides presentations.
- This tool is Shared Drive-safe and uses `supportsAllDrives` / `includeItemsFromAllDrives`.
- It does not write anything back to Google Drive.
- It does not do course-specific renaming or placement.
