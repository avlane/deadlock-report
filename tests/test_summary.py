import os
import unittest

from deadlock_report.parser import parse_deadlocks
from deadlock_report.summary import render_summary, summarize

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_all(*names):
    text = ""
    for name in names:
        with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
            text += f.read()
    return parse_deadlocks(text)


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.deadlocks = load_all("deadlock_key.xml", "deadlock_key.xml", "deadlock_parallel.xml", "deadlock_page.xml")
        self.summary = summarize(self.deadlocks)

    def test_totals(self):
        self.assertEqual(self.summary["total"], 4)
        self.assertEqual(self.summary["parallel"], 1)

    def test_objects_are_counted_once_per_deadlock(self):
        objects = dict(self.summary["objects"])
        self.assertEqual(objects["Sales.dbo.Orders"], 2)
        self.assertEqual(objects["Audit.dbo.AuditLog"], 1)

    def test_victim_procedures(self):
        victims = dict(self.summary["victims"])
        self.assertEqual(victims["Sales.dbo.usp_UpdateOrderStatus"], 2)
        self.assertEqual(victims["Sales.dbo.usp_MonthlySalesReport"], 1)
        self.assertEqual(victims["Audit.dbo.usp_LogEvent"], 1)

    def test_apps(self):
        self.assertEqual(dict(self.summary["apps"])["OrdersWeb"], 2)

    def test_most_common_first(self):
        self.assertEqual(self.summary["objects"][0][1], 2)

    def test_render(self):
        text = render_summary(self.summary, top=2)
        self.assertTrue(text.startswith("4 deadlock(s), 1 of them intra-query parallelism"))
        self.assertIn("Victim procedures", text)

    def test_empty(self):
        text = render_summary(summarize([]))
        self.assertIn("0 deadlock(s)", text)


if __name__ == "__main__":
    unittest.main()
