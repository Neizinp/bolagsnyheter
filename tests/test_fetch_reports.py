import unittest
import xml.etree.ElementTree as ET

from scripts.fetch_reports import newest_reports, period_key, report_from_item


class ReportTests(unittest.TestCase):
    def item(self, title):
        item = ET.Element("item")
        for key, value in {
            "title": title,
            "link": "https://news.cision.com/se/sandvik/r/rapport,c123",
            "pubDate": "Wed, 22 Oct 2025 06:00:00 GMT",
            "description": "Intäkter 100 miljoner",
        }.items():
            ET.SubElement(item, key).text = value
        return item

    def test_report_and_company(self):
        report = report_from_item(self.item("Delårsrapport tredje kvartalet 2025"))
        self.assertEqual(report["id"], "sandvik")
        self.assertEqual(report["name"], "Sandvik")
        self.assertEqual(period_key(report), "2025-q3")

    def test_excludes_report_announcement(self):
        self.assertIsNone(report_from_item(self.item("Inbjudan till presentation av delårsrapport")))

    def test_same_quarter_in_different_title_formats(self):
        first = report_from_item(self.item("Delårsrapport Q3 2025"))
        second = report_from_item(self.item("Delårsrapport januari-september 2025"))
        self.assertEqual(period_key(first), period_key(second))

    def test_result_titles(self):
        first = report_from_item(self.item("Verisure Q3 2025 Resultat"))
        second = report_from_item(self.item("Verisure rapporterar resultat för tredje kvartalet 2025"))
        self.assertEqual(period_key(first), period_key(second))
        self.assertIsNone(report_from_item(self.item("Resultat av extra bolagsstämma")))

    def test_new_report_replaces_oldest(self):
        quarters = [("2025-02-12", "Bokslutskommuniké 2024"), ("2025-04-25", "Delårsrapport Q1 2025"),
                    ("2025-07-18", "Delårsrapport Q2 2025"), ("2025-10-22", "Delårsrapport Q3 2025"),
                    ("2026-02-11", "Bokslutskommuniké 2025")]
        reports = {}
        for index, (date, title) in enumerate(quarters):
            url = f"https://news.cision.com/se/sandvik/r/rapport,c{index}"
            reports[url] = {"id": "sandvik", "title": title, "url": url, "published": f"{date}T06:00:00+00:00"}
        titles = [report["title"] for report in newest_reports(reports)]
        self.assertEqual(titles, [title for _, title in reversed(quarters[1:])])


if __name__ == "__main__":
    unittest.main()