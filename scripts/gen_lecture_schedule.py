#!/usr/bin/env python3
"""Generate lecture schedules from academic calendars and course metadata."""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
COURSE_INFO = ROOT / "course-info"
LECTURE_SCHEDULES_DIR = COURSE_INFO / "lecture-schedules"
DAY_TO_INDEX = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate per-course lecture schedules.")
    parser.add_argument("--slug", help="Limit output to the given course slug.")
    parser.add_argument("--term", help="Limit output to the given term identifier (e.g., spring_2026).")
    return parser.parse_args()


def load_course_config() -> list[dict]:
    config_path = COURSE_INFO / "courses.yaml"
    if not config_path.exists():
        raise SystemExit("Missing course-info/courses.yaml")
    data = yaml.safe_load(config_path.read_text()) or {}
    return data.get("courses", [])


def load_standard_calendars() -> dict[str, dict]:
    catalogs: dict[str, dict] = {}
    for calendar_path in sorted(COURSE_INFO.glob("ay-*.json")):
        data = json.loads(calendar_path.read_text())
        academic_year = data.get("academic_year")
        for term in data.get("terms", []):
            term_name = term.get("term")
            if not term_name:
                continue
            catalogs[term_name] = {
                "academic_year": academic_year,
                "term": term,
            }
    return catalogs


def parse_iso(value: str) -> date:
    return date.fromisoformat(value)


def expand_no_class_ranges(term: dict) -> list[tuple[date, date]]:
    ranges: list[tuple[date, date]] = []
    for entry in term.get("noClass", []):
        start = entry.get("start") or entry.get("date")
        end = entry.get("end") or start
        if not start:
            continue
        start_date = parse_iso(start)
        end_date = parse_iso(end)
        ranges.append((start_date, end_date))
    return ranges


def load_substitute_days(term: dict) -> dict[date, str]:
    subs: dict[date, str] = {}
    for entry in term.get("substituteDays", []):
        entry_date = entry.get("date")
        schedule = entry.get("schedule")
        if not entry_date or not schedule:
            continue
        try:
            subs[parse_iso(entry_date)] = schedule.title()
        except ValueError:
            continue
    return subs


def convert_lecture_days(days: Iterable[str]) -> set[int]:
    normalized = set()
    for day in days:
        day = day.title()
        if day not in DAY_TO_INDEX:
            raise ValueError(f"Unknown lecture day: {day}")
        normalized.add(DAY_TO_INDEX[day])
    return normalized


def between_dates(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def should_skip_day(
    candidate: date,
    lecture_weekdays: set[int],
    no_class_ranges: list[tuple[date, date]],
    substitutes: dict[date, str],
) -> bool:
    for start, end in no_class_ranges:
        if start <= candidate <= end:
            return True

    actual = candidate.weekday()
    substitute = substitutes.get(candidate)
    schedule_weekday = None
    if substitute:
        schedule_weekday = DAY_TO_INDEX.get(substitute.title())
    runs_on_actual = actual in lecture_weekdays
    runs_on_schedule = schedule_weekday in lecture_weekdays if schedule_weekday is not None else False

    if substitute and runs_on_actual and not runs_on_schedule:
        return True

    meets_by_actual = runs_on_actual
    meets_by_schedule = schedule_weekday is not None and schedule_weekday in lecture_weekdays
    return not (meets_by_actual or meets_by_schedule)


def generate_lecture_dates(
    start_date: date,
    end_date: date,
    lecture_weekdays: set[int],
    no_class_ranges: list[tuple[date, date]],
    substitutes: dict[date, str],
) -> list[date]:
    lectures: list[date] = []
    for slot in between_dates(start_date, end_date):
        if should_skip_day(slot, lecture_weekdays, no_class_ranges, substitutes):
            continue
        lectures.append(slot)
    return lectures



def main() -> None:
    args = parse_args()
    courses = load_course_config()
    calendars = load_standard_calendars()
    if not courses:
        raise SystemExit("No courses found in course-info/courses.yaml")

    LECTURE_SCHEDULES_DIR.mkdir(parents=True, exist_ok=True)
    today_str = date.today().isoformat()

    for course in courses:
        slug = course.get("slug")
        if not slug:
            continue
        if args.slug and args.slug != slug:
            continue
        lecture_days = course.get("lecture_days", [])
        if not lecture_days:
            continue
        weekday_set = convert_lecture_days(lecture_days)

        term_entries = course.get("terms", [])
        for term_entry in term_entries:
            term_name = term_entry.get("term")
            if args.term and args.term != term_name:
                continue
            if not term_name:
                continue
            term_calendar = calendars.get(term_name)
            if not term_calendar:
                raise SystemExit(f"No calendar data for term {term_name}")
            start = term_entry.get("start")
            end = term_entry.get("end")
            if not start or not end:
                raise SystemExit(f"Missing start/end for {slug} {term_name}")
            start_date = parse_iso(start)
            end_date = parse_iso(end)
            term_data = term_calendar.get("term", {})
            no_class_ranges = expand_no_class_ranges(term_data)
            substitutes = load_substitute_days(term_data)
            lecture_days_list = generate_lecture_dates(
                start_date, end_date, weekday_set, no_class_ranges, substitutes
            )
            output = {
                "course": slug,
                "term": term_name,
                "generated": today_str,
                "lectures": [
                    {"number": idx + 1, "date": day.isoformat()} for idx, day in enumerate(lecture_days_list)
                ],
            }
            out_path = LECTURE_SCHEDULES_DIR / f"{slug}-{term_name}.yaml"
            with out_path.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(output, handle, sort_keys=False)

            first_date = lecture_days_list[0].isoformat() if lecture_days_list else "n/a"
            last_date = lecture_days_list[-1].isoformat() if lecture_days_list else "n/a"
            print(
                f"{slug} {term_name}: {len(lecture_days_list)} lectures ({first_date} - {last_date})"
            )


if __name__ == "__main__":
    main()
