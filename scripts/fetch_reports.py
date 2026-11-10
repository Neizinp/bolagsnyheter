#!/usr/bin/env python3
"""Collect report announcements from Cision's Swedish RSS search."""

import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "reports.json"
FEED_URL = "https://news.cision.com/se/ListItems"
QUERIES = ("delårsrapport", "kvartalsrapport", "bokslutskommuniké")
REPORT = re.compile(r"delårsrapport|kvartalsrapport|bokslutskommuniké", re.I)
EXCLUDE = re.compile(r"kallelse|inbjudan|webcast|presentation|publicer(?:as|ing)|tidigarelägg|senarelägg|datum|påminnelse|kalender", re.I)


def get_items(query, page, company=None):
    params = {"format": "rss", "q": query, "pageIx": page}
    if company:
        params["n"] = company
    params = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{FEED_URL}?{params}", headers={"User-Agent": "Bolagsrapporter/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())
    return root.findall(".//item")


def report_from_item(item):
    title = item.findtext("title", "").strip()
    url = item.findtext("link", "").strip()
    parts = urllib.parse.urlparse(url).path.strip("/").split("/")
    if not REPORT.search(title) or EXCLUDE.search(title) or len(parts) < 4 or parts[0] != "se" or parts[2] != "r":
        return None
    try:
        published = parsedate_to_datetime(item.findtext("pubDate", "")).astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None
    if published > datetime.now(timezone.utc):
        return None
    slug = parts[1]
    description = re.sub(r"\s+", " ", item.findtext("description", "")).strip()
    return {"id": slug, "name": slug.replace("--publ-", "").replace("-", " ").strip().title(),
            "title": title, "url": url, "published": published.isoformat(), "description": description[:350]}


def period_key(report):
    title = report["title"].lower()
    year = re.search(r"20\d{2}", title)
    quarter = re.search(r"\bq\s*([1-4])\b|\b([1-4])(?:a|:e)?\s+kvartal|\b(första|andra|tredje|fjärde)\s+kvartal", title)
    months = {"mars": "1", "juni": "2", "september": "3", "december": "4"}
    value = next((part for part in quarter.groups() if part), None) if quarter else None
    value = {"första": "1", "andra": "2", "tredje": "3", "fjärde": "4"}.get(value, value)
    if not value:
        value = next((number for month, number in months.items() if month in title), None)
    if not value and "bokslutskommuniké" in title:
        value = "4"
    if value and year:
        return f"{year.group()}-q{value}"
    return report["url"]


def main():
    company = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--company" else None
    pages = 1 if company else int(sys.argv[1]) if len(sys.argv) > 1 else 5
    old = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    reports = {report["url"]: report for report in old.get("reports", [])}
    failure = None
    try:
        for query in QUERIES:
            for page in range(1, pages + 1):
                items = get_items(query, page, company)
                if not items:
                    break
                for item in items:
                    report = report_from_item(item)
                    if report and (not company or report["id"] == company):
                        reports[report["url"]] = report
                time.sleep(1)
            print(f"{query}: {page} sidor", flush=True)
    except (OSError, ET.ParseError) as error:
        failure = error
    unique = {}
    for report in sorted(reports.values(), key=lambda row: row["published"], reverse=True):
        unique.setdefault((report["id"], period_key(report)), report)
    counts = {}
    result = []
    for report in unique.values():
        counts[report["id"]] = counts.get(report["id"], 0) + 1
        if counts[report["id"]] <= 4:
            result.append(report)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"updatedAt": datetime.now(timezone.utc).isoformat(), "reports": result}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(result)} rapporter från {len(counts)} nyhetsrum")
    if failure:
        raise SystemExit(f"Hämtningen avbröts: {failure}")


if __name__ == "__main__":
    main()