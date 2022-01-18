import json
import os
import unittest

from deadlock_report.export import deadlock_to_dict, to_json
from deadlock_report.parser import parse_deadlocks

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_all(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return parse_deadlocks(f.read())


class ExportTests(unittest.TestCase):
    def test_dict_has_computed_fields(self):
        data = deadlock_to_dict(load_all("deadlock_key.xml")[0])
        self.assertEqual(data["timestamp"], "2020-01-14T10:22:31.123Z")
        self.assertFalse(data["is_parallel"])
        self.assertEqual(data["cycle"], ["process1f6a2b8c8", "process1f6a2c4e8"])
        self.assertEqual(data["processes"][1]["procedure"], "Sales.dbo.usp_AddOrderLine")
        self.assertTrue(data["processes"][0]["statement"].startswith("UPDATE dbo.OrderLines"))

    def test_json_round_trip(self):
        decoded = json.loads(to_json(load_all("ring_buffer.xml")))
        self.assertEqual(len(decoded), 2)
        self.assertEqual(decoded[1]["resources"][0]["kind"], "ridlock")
        self.assertEqual(decoded[0]["victims"], ["process2a10b1ba8"])

    def test_owners_and_waiters_are_included(self):
        data = deadlock_to_dict(load_all("deadlock_page.xml")[0])
        self.assertEqual(data["resources"][0]["waiters"][0]["request_type"], "convert")


if __name__ == "__main__":
    unittest.main()
