import os
import unittest

from deadlock_report.hints import suggest
from deadlock_report.parser import parse_deadlock

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return parse_deadlock(f.read())


def contains(hints, text):
    return any(text in h for h in hints)


class HintTests(unittest.TestCase):
    def test_opposite_lock_order(self):
        hints = suggest(load("deadlock_key.xml"))
        self.assertTrue(contains(hints, "opposite orders"))
        self.assertTrue(contains(hints, "Sales.dbo.Orders and Sales.dbo.OrderLines"))

    def test_readers_blocked_under_read_committed(self):
        hints = suggest(load("deadlock_no_stack.xml"))
        self.assertTrue(contains(hints, "READ_COMMITTED_SNAPSHOT"))

    def test_updates_are_not_readers(self):
        self.assertFalse(contains(suggest(load("deadlock_key.xml")), "READ_COMMITTED_SNAPSHOT"))

    def test_parallel(self):
        hints = suggest(load("deadlock_parallel.xml"))
        self.assertEqual(len(hints), 1)
        self.assertIn("MAXDOP 1", hints[0])

    def test_page_locks_and_open_transactions(self):
        hints = suggest(load("deadlock_page.xml"))
        self.assertTrue(contains(hints, "lock escalation"))
        self.assertTrue(contains(hints, "trancount above 1"))
        self.assertTrue(contains(hints, "Both sides run Audit.dbo.usp_LogEvent"))

    def test_heap(self):
        from deadlock_report.parser import parse_deadlocks
        with open(os.path.join(FIXTURES, "ring_buffer.xml"), encoding="utf-8") as f:
            rid = parse_deadlocks(f.read())[1]
        self.assertTrue(contains(suggest(rid), "heap"))


if __name__ == "__main__":
    unittest.main()
