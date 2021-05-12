import os
import unittest

from deadlock_report.html_report import render_html
from deadlock_report.parser import parse_deadlocks

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_all(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return parse_deadlocks(f.read())


class HtmlTests(unittest.TestCase):
    def setUp(self):
        self.html = render_html(load_all("deadlock_key.xml"))

    def test_document_shell(self):
        self.assertTrue(self.html.startswith("<!DOCTYPE html>"))
        self.assertIn("<title>Deadlock report</title>", self.html)

    def test_heading_and_victim(self):
        self.assertIn("<h2>Deadlock 1 of 1 at 2020-01-14 10:22:31.123 UTC</h2>", self.html)
        self.assertIn("<strong>Victim (rolled back):</strong> spid 57", self.html)

    def test_cycle(self):
        self.assertIn("<strong>Cycle:</strong> spid 57 waits for spid 62 waits for spid 57", self.html)

    def test_tables(self):
        self.assertIn("<td>spid 57 (victim)</td>", self.html)
        self.assertIn("<td>Sales.dbo.Orders / PK_Orders</td>", self.html)
        self.assertIn("<td>X (Exclusive)</td>", self.html)

    def test_several_deadlocks(self):
        html = render_html(load_all("ring_buffer.xml"))
        self.assertEqual(html.count("<section>"), 2)


if __name__ == "__main__":
    unittest.main()
