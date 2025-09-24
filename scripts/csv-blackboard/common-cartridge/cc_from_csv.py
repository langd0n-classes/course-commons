#!/usr/bin/env python3
"""
cc_from_csv.py — Generate a minimal IMS Common Cartridge (v1.1-ish) of placeholder items from a CSV.

Creates a package that imports into Blackboard Ultra as content items (webcontent) with titles
and placeholder dates in the item body. Actual Ultra due/availability dates may need manual edit
post-import because LMS handling of dates in CC varies.

Usage:
  python cc_from_csv.py --csv INPUT.csv --out OUTPUT.imscc [--config config.json] [--limit N]

Config JSON example (keys are column names in your CSV):

{
  "title_col": "Assignment/lecture name",
  "type_col": "Type",
  "due_date_col": "Due Date",
  "release_date_col": "Release Date",
  "include_types": ["Assignment", "Assessment", "Lab"],
  "default_points": 0,
  "organization_title": "DS-100 Placeholder Assignments",
  "cartridge_version": "1.1"
}
"""
import argparse, json, os, zipfile, html
from datetime import datetime
from pathlib import Path
import pandas as pd


DEFAULTS = {
  "title_col": "Assignment/lecture name",
  "type_col": "Type",
  "due_date_col": "Due Date",
  "release_date_col": "Release Date",
  "include_types": ["Assignment", "Assessment", "Lab"],
  "default_points": 0,
  "organization_title": "Placeholder Assignments",
  "cartridge_version": "1.1"
}


def parse_date_safe(x):
    if pd.isna(x) or str(x).strip() == "":
        return None
    s = str(x).strip()
    fmts = ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%b %d, %Y", "%B %d, %Y", "%m/%d/%y"]
    for f in fmts:
        try:
            return datetime.strptime(s, f).strftime("%Y-%m-%d")
        except Exception:
            pass
    return s


def make_manifest(items, org_title):
    ns_imscp = "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
    ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
    schema_loc = (
        "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1 "
        "https://www.imsglobal.org/profile/cc/ccv1p1/imscp_v1p1.xsd"
    )
    org_items = []
    res_xml = []
    for i, it in enumerate(items, start=1):
        href = f"items/{it['id']}/index.html"
        org_items.append(
            f'      <item identifier="item{i:04d}" identifierref="{it["id"]}">\n'
            f'        <title>{html.escape(it["title"])}</title>\n'
            f'      </item>'
        )
        res_xml.append(
            f'    <resource identifier="{it["id"]}" type="webcontent" href="{href}">\n'
            f'      <file href="{href}" />\n'
            f'    </resource>'
        )
    manifest = f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="MANIFEST1"
  xmlns="{ns_imscp}"
  xmlns:xsi="{ns_xsi}"
  xsi:schemaLocation="{schema_loc}">
  <metadata>
    <schema>IMS Content</schema>
    <schemaversion>1.1.0</schemaversion>
  </metadata>
  <organizations default="ORG1">
    <organization identifier="ORG1">
      <title>{html.escape(org_title)}</title>
{chr(10).join(org_items)}
    </organization>
  </organizations>
  <resources>
{chr(10).join(res_xml)}
  </resources>
</manifest>'''
    return manifest


def make_item_html(it):
    return (
        "<html><head><meta charset=\"utf-8\"><title>{t}</title></head>\n"
        "<body>\n"
        "  <h1>{t}</h1>\n"
        "  <ul>\n"
        "    <li>Type: {typ}</li>\n"
        "    <li>Points (placeholder): {pts}</li>\n"
        "    <li>Release date (placeholder): {rel}</li>\n"
        "    <li>Due date (placeholder): {due}</li>\n"
        "  </ul>\n"
        "  <p>This is a placeholder item imported via Common Cartridge. Replace with the actual assignment details.</p>\n"
        "</body></html>"
    ).format(
        t=html.escape(it["title"]),
        typ=html.escape(it["type"]),
        pts=it["points"],
        rel=html.escape(it["release"] or "—"),
        due=html.escape(it["due"] or "—"),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Input CSV path")
    ap.add_argument("--out", required=True, help="Output .imscc zip path")
    ap.add_argument("--config", help="JSON config path (optional)")
    ap.add_argument("--limit", type=int, help="Limit the number of items for a small test run")
    args = ap.parse_args()

    cfg = DEFAULTS.copy()
    if args.config and os.path.exists(args.config):
        with open(args.config) as f:
            cfg.update(json.load(f))

    df = pd.read_csv(args.csv)
    mask = df[cfg["type_col"]].astype(str).str.strip().isin(cfg["include_types"])
    items_df = df[mask].copy()

    items = []
    for _, row in items_df.iterrows():
        if args.limit is not None and len(items) >= args.limit:
            break
        title = str(row.get(cfg["title_col"], "")).strip()
        if not title:
            continue
        due = parse_date_safe(row.get(cfg["due_date_col"]))
        rel = parse_date_safe(row.get(cfg["release_date_col"]))
        typ = str(row.get(cfg["type_col"], "")).strip()
        items.append({
            "id": f"res{len(items)+1:04d}",
            "title": title,
            "type": typ,
            "due": due,
            "release": rel,
            "points": cfg["default_points"]
        })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imsmanifest.xml", make_manifest(items, cfg["organization_title"]))
        for it in items:
            zf.writestr(f"items/{it['id']}/index.html", make_item_html(it))

    # Optional ICS alongside, if dates exist
    any_due = any(bool(it["due"]) for it in items)
    if any_due:
        ics_lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CSV to CC//EN"]
        for it in items:
            if not it["due"]:
                continue
            ics_lines += [
                "BEGIN:VEVENT",
                f"UID:{uuid4()}",
                f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART;VALUE=DATE:{it['due'].replace('-', '')}",
                f"SUMMARY:{it['title']} (Due)",
                "END:VEVENT"
            ]
        ics_lines.append("END:VCALENDAR")
        with open(out_path.with_suffix(".ics"), "w") as f:
            f.write("\n".join(ics_lines))

    print(f"Wrote {out_path} with {len(items)} items.")
    if any_due:
        print(f"Wrote calendar: {out_path.with_suffix('.ics')}")


if __name__ == "__main__":
    from uuid import uuid4
    main()