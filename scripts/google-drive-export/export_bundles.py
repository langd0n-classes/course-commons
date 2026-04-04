#!/usr/bin/env python3
"""Export Google Slides decks from Drive into a labeled local bundle."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from drive_client import DriveClient, DriveClientError

GOOGLE_SLIDES_MIME = "application/vnd.google-apps.presentation"
EXPORTS = (
    ("application/pdf", ".pdf"),
    ("text/plain", ".txt"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export one Google Slides deck or all direct-child decks in a Drive folder "
            "into a labeled local bundle with metadata."
        )
    )
    parser.add_argument("--label", help="Run label, e.g. ds551-202601-S26")
    parser.add_argument("--file", help="Google Slides file URL or file ID")
    parser.add_argument("--folder", help="Google Drive folder URL or folder ID")
    parser.add_argument(
        "--output-dir",
        help=(
            "Target directory for the export bundle. Defaults to a generated temp directory "
            "under the system temp root."
        ),
    )
    return parser.parse_args()


def prompt_if_missing(args: argparse.Namespace) -> argparse.Namespace:
    if args.file or args.folder:
        return args

    print("No --file or --folder provided; entering interactive mode.")
    if not args.label:
        args.label = input("Label: ").strip()

    mode = ""
    while mode not in {"file", "folder"}:
        mode = input("Export one file or a folder? [file/folder]: ").strip().lower()

    target = input("Google Drive file/folder URL or ID: ").strip()
    out = input("Output directory [default: generated temp dir]: ").strip()
    if out:
        args.output_dir = out

    if mode == "file":
        args.file = target
    else:
        args.folder = target
    return args


def require_valid_args(args: argparse.Namespace) -> None:
    if not args.label:
        raise SystemExit("ERROR: --label is required.")
    if bool(args.file) == bool(args.folder):
        raise SystemExit("ERROR: provide exactly one of --file or --folder.")


def normalize_target_id(raw: str) -> str:
    raw = raw.strip()
    patterns = [
        r"/d/([a-zA-Z0-9_-]+)",
        r"/folders/([a-zA-Z0-9_-]+)",
        r"[?&]id=([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            return match.group(1)
    return raw


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-.") or "bundle"


def safe_filename(title: str, suffix: str) -> str:
    base = re.sub(r"[\\/]+", "_", title).strip() or "untitled"
    return f"{base}{suffix}"


def resolve_output_dir(label: str, output_dir: str | None) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    if output_dir:
        path = Path(output_dir).expanduser().resolve()
        if path.exists():
            if not path.is_dir():
                raise FileExistsError(f"{path} exists and is not a directory")
            if any(path.iterdir()):
                raise FileExistsError(f"{path} already exists and is not empty")
            return path
    else:
        root = Path(tempfile.gettempdir()) / "google-drive-export-bundles"
        path = root / f"{slugify(label)}-{timestamp}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def gather_targets(client: DriveClient, file_id: str | None, folder_id: str | None) -> tuple[str, str, list[dict[str, Any]]]:
    if file_id:
        meta = client.get_file(file_id)
        if meta.get("mimeType") != GOOGLE_SLIDES_MIME:
            raise SystemExit(
                f"ERROR: target file is not a Google Slides presentation: {meta.get('name')} ({meta.get('mimeType')})"
            )
        return "file", file_id, [meta]

    assert folder_id is not None
    folder_meta = client.get_file(folder_id)
    items = client.list_child_items(folder_id)
    slides = [item for item in items if item.get("mimeType") == GOOGLE_SLIDES_MIME]
    slides.sort(key=lambda item: item.get("name", ""))
    return "folder", folder_meta.get("id", folder_id), slides


def export_targets(client: DriveClient, targets: list[dict[str, Any]], output_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in targets:
        title = target["name"]
        file_record: dict[str, Any] = {
            "file_id": target["id"],
            "title": title,
            "drive_mime_type": target.get("mimeType"),
            "web_view_link": target.get("webViewLink"),
            "created_time": target.get("createdTime"),
            "modified_time": target.get("modifiedTime"),
            "exports": [],
        }

        for export_mime, suffix in EXPORTS:
            payload = client.export_file_bytes(target["id"], export_mime)
            filename = safe_filename(title, suffix)
            dest = output_dir / filename
            dest.write_bytes(payload)
            file_record["exports"].append(
                {
                    "mime_type": export_mime,
                    "filename": filename,
                    "bytes": len(payload),
                }
            )

        records.append(file_record)
    return records


def write_metadata(
    *,
    output_dir: Path,
    label: str,
    source_mode: str,
    source_input: str,
    resolved_source_id: str,
    records: list[dict[str, Any]],
) -> Path:
    metadata = {
        "label": label,
        "downloaded_at": datetime.now(UTC).isoformat(),
        "source_mode": source_mode,
        "source_input": source_input,
        "resolved_source_id": resolved_source_id,
        "file_count": len(records),
        "files": records,
    }
    path = output_dir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    args = prompt_if_missing(parse_args())
    require_valid_args(args)

    source_input = args.file or args.folder
    assert source_input is not None

    try:
        client = DriveClient()
    except DriveClientError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        output_dir = resolve_output_dir(args.label, args.output_dir)
        source_mode, resolved_source_id, targets = gather_targets(
            client,
            file_id=normalize_target_id(args.file) if args.file else None,
            folder_id=normalize_target_id(args.folder) if args.folder else None,
        )
        records = export_targets(client, targets, output_dir)
        metadata_path = write_metadata(
            output_dir=output_dir,
            label=args.label,
            source_mode=source_mode,
            source_input=source_input,
            resolved_source_id=resolved_source_id,
            records=records,
        )
    except FileExistsError:
        print("ERROR: output directory already exists; choose a different --output-dir.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote bundle to {output_dir}")
    print(f"Wrote metadata to {metadata_path}")
    print(f"Exported {len(records)} presentation(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
