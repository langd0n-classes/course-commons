#!/usr/bin/env python3
"""Google Drive client helpers for Shared Drive-safe read/export workflows."""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class DriveClientError(RuntimeError):
    """Raised when client setup or Drive API calls fail."""


class DriveClient:
    def __init__(self) -> None:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            raise DriveClientError(
                "GOOGLE_APPLICATION_CREDENTIALS is not set. Point it to a readable service account JSON file."
            )

        cred_file = Path(cred_path).expanduser()
        if not cred_file.exists() or not cred_file.is_file():
            raise DriveClientError(f"Credentials file not found: {cred_file}")
        if not os.access(cred_file, os.R_OK):
            raise DriveClientError(f"Credentials file is not readable: {cred_file}")

        scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        credentials = service_account.Credentials.from_service_account_file(
            str(cred_file), scopes=scopes
        )
        self.service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    def get_file(self, file_id: str) -> dict[str, Any]:
        return (
            self.service.files()
            .get(
                fileId=file_id,
                fields=(
                    "id, name, mimeType, createdTime, modifiedTime, webViewLink, "
                    "iconLink, parents"
                ),
                supportsAllDrives=True,
            )
            .execute()
        )

    def list_child_items(self, folder_id: str) -> list[dict[str, Any]]:
        query = f"'{folder_id}' in parents and trashed = false"
        items: list[dict[str, Any]] = []
        page_token = None

        while True:
            response = (
                self.service.files()
                .list(
                    q=query,
                    pageSize=1000,
                    fields=(
                        "nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, webViewLink)"
                    ),
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    corpora="allDrives",
                    pageToken=page_token,
                )
                .execute()
            )
            items.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return items

    def export_file_bytes(self, file_id: str, mime_type: str) -> bytes:
        request = self.service.files().export_media(fileId=file_id, mimeType=mime_type)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()
