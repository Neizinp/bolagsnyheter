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
REPORT = re.compile(r"delårsrapport|kvartalsrapport|bokslutskommuniké|\bq[1-4]\s*20\d{2}\s+resultat|resultat för (?:första|andra|tredje|fjärde) kvartalet", re.I)
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


def newest_reports(reports):
    unique = {}
    for report in sorted(reports.values(), key=lambda row: row["published"], reverse=True):
        unique.setdefault((report["id"], period_key(report)), report)
    counts = {}
    result = []
    for report in unique.values():
        counts[report["id"]] = counts.get(report["id"], 0) + 1
        if counts[report["id"]] <= 4:
            result.append(report)
    return result


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


def collect(reports, group, pages):
    current = ",".join(group) if group[0] else None
    for query in QUERIES:
        for page in range(1, pages + 1):
            items = get_items(query, page, current)
            if not items:
                break
            for item in items:
                report = report_from_item(item)
                if report and (not current or report["id"] in group):
                    reports[report["url"]] = report
            time.sleep(1)
            if current and all(count >= 4 for name, count in report_counts(reports, group).items()):
                break


def report_counts(reports, ids=None):
    counts = {name: 0 for name in ids or []}
    for report in newest_reports(reports):
        counts[report["id"]] = counts.get(report["id"], 0) + 1
    return counts


def save(reports):
    result = newest_reports(reports)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"updatedAt": datetime.now(timezone.utc).isoformat(), "reports": result}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return result


def main():
    backfill = len(sys.argv) > 1 and sys.argv[1] == "--backfill"
    company = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--company" else None
    pages = 3 if company else 1 if backfill else int(sys.argv[1]) if len(sys.argv) > 1 else 5
    old = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    reports = {report["url"]: report for report in old.get("reports", [])}
    failure = None
    current = company
    try:
        if not backfill:
            collect(reports, [company], pages)
        else:
            start = sys.argv[2] if len(sys.argv) > 2 else ""
            missing = sorted(name for name, count in report_counts(reports).items() if count < 4 and name >= start)
            groups = [missing[index:index + 4] for index in range(0, len(missing), 4)]
            for index, group in enumerate(groups, 1):
                current = ",".join(group)
                collect(reports, group, 1)
                print(f"{index}/{len(groups)}: {current}", flush=True)
                if index % 10 == 0:
                    save(reports)
            missing = [name for name in missing if report_counts(reports, [name])[name] < 4]
            for index, name in enumerate(missing, 1):
                current = name
                collect(reports, [name], 3)
                print(f"{index}/{len(missing)}: {name} {report_counts(reports, [name])[name]}", flush=True)
                if index % 10 == 0:
                    save(reports)
    except (OSError, ET.ParseError) as error:
        failure = error
    result = save(reports)
    counts = report_counts(reports)
    print(f"{len(result)} rapporter från {len(counts)} nyhetsrum, {sum(count < 4 for count in counts.values())} med färre än fyra")
    if failure:
        raise SystemExit(f"Hämtningen avbröts vid {current}: {failure}")


if __name__ == "__main__":
    main()