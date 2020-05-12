import os
import unittest

from deadlock_report.analysis import find_cycle, wait_for_edges
from deadlock_report.parser import parse_deadlock, parse_deadlocks

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return parse_deadlock(f.read())


class CycleTests(unittest.TestCase):
    def test_two_way_cycle(self):
        d = load("deadlock_key.xml")
        self.assertEqual(wait_for_edges(d), {"process1f6a2c4e8": ["process1f6a2b8c8"],
                                             "process1f6a2b8c8": ["process1f6a2c4e8"]})
        self.assertEqual(find_cycle(d), ["process1f6a2b8c8", "process1f6a2c4e8"])

    def test_three_way_cycle(self):
        d = load("deadlock_three_way.xml")
        cycle = find_cycle(d)
        self.assertEqual([d.process(pid).spid for pid in cycle], [101, 104, 109])

    def test_parallel_cycle_goes_through_exchanges(self):
        d = load("deadlock_parallel.xml")
        self.assertEqual(len(find_cycle(d)), 3)

    def test_no_cycle(self):
        d = load("deadlock_key.xml")
        d.resources = d.resources[:1]
        self.assertEqual(find_cycle(d), [])


if __name__ == "__main__":
    unittest.main()
