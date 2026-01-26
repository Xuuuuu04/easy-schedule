#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from datetime import date

from backend.service import (
    count_courses_filtered,
    query_courses_filtered,
    bulk_update_courses_filtered,
    bulk_delete_courses_filtered,
)


def timed(label, fn):
    t0 = time.perf_counter()
    out = fn()
    dt = (time.perf_counter() - t0) * 1000
    print(f"{label}: {dt:.1f}ms")
    return out


def main():
    today = date.today().isoformat()
    date_range = f"{today},{today}"

    print("=== Bulk Tools Perf Probe ===")
    print(f"date_range={date_range}")
    print()

    cnt = timed(
        "count_courses_filtered(today)",
        lambda: count_courses_filtered(date_range=date_range),
    )
    print(f"matched={cnt}")
    print()

    courses = timed(
        "query_courses_filtered(today, limit=20)",
        lambda: query_courses_filtered(date_range=date_range, limit=20),
    )
    print(f"rows={len(courses)}")
    if courses:
        c = courses[0]
        print(f"sample: {c.title} | {c.student_name} | {c.start}~{c.end}")
    print()

    if os.environ.get("BULK_PERF_DANGEROUS") == "1":
        print("DANGEROUS MODE: enabled")
        timed(
            "bulk_update_courses_filtered(__nomatch__)",
            lambda: bulk_update_courses_filtered(title_pattern="__nomatch__", new_location=""),
        )
        timed(
            "bulk_delete_courses_filtered(__nomatch__)",
            lambda: bulk_delete_courses_filtered(title_pattern="__nomatch__"),
        )
    else:
        print("DANGEROUS MODE: disabled (set BULK_PERF_DANGEROUS=1 to run update/delete)")


if __name__ == "__main__":
    main()

