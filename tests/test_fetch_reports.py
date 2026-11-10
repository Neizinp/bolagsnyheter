import unittest
import xml.etree.ElementTree as ET

from scripts.fetch_reports import period_key, report_from_item


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


if __name__ == "__main__":
    unittest.main()