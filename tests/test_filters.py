import os
import unittest

from deadlock_report import filters
from deadlock_report.parser import parse_deadlocks

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

with open(os.path.join(FIXTURES, "ring_buffer.xml"), encoding="utf-8") as _f:
    RING = parse_deadlocks(_f.read())  # Inventory (3-way) then Staging (RID)


class FilterTests(unittest.TestCase):
    def test_by_database(self):
        found = filters.apply(RING, database="inventory")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].processes[0].database, "Inventory")

    def test_database_name_is_not_a_prefix_match_on_other_names(self):
        self.assertEqual(filters.apply(RING, database="Stag"), [])

    def test_by_object(self):
        self.assertEqual(len(filters.apply(RING, object_name="importrows")), 1)
        self.assertEqual(len(filters.apply(RING, object_name="Products")), 1)

    def test_both_filters_must_match(self):
        self.assertEqual(filters.apply(RING, database="Inventory", object_name="ImportRows"), [])

    def test_no_filters(self):
        self.assertEqual(filters.apply(RING), RING)


if __name__ == "__main__":
    unittest.main()
