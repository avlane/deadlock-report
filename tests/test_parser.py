import os
import unittest

from deadlock_report.parser import parse_deadlock

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.deadlock = parse_deadlock(fixture("deadlock_key.xdl"))

    def test_two_processes(self):
        self.assertEqual([p.spid for p in self.deadlock.processes], [57, 62])

    def test_process_attributes(self):
        p = self.deadlock.processes[0]
        self.assertEqual(p.id, "process1f6a2b8c8")
        self.assertEqual(p.login, "CORP\\svc_orders")
        self.assertEqual(p.host, "APP01")
        self.assertEqual(p.app, "OrdersWeb")
        self.assertEqual(p.database, "Sales")
        self.assertEqual(p.wait_time_ms, 4521)
        self.assertEqual(p.isolation_level, "read committed (2)")
        self.assertEqual(p.trancount, 2)

    def test_wait_resource(self):
        self.assertEqual(self.deadlock.processes[1].wait_resource, "KEY: 5:72057594043498496 (a1b2c3d4e5f6)")

    def test_event_wrapper_is_found(self):
        wrapped = parse_deadlock(fixture("deadlock_key.xml"))
        self.assertEqual(len(wrapped.processes), 2)

    def test_not_a_deadlock(self):
        with self.assertRaises(ValueError):
            parse_deadlock("<event/>")


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.deadlock = parse_deadlock(fixture("deadlock_key.xdl"))

    def test_victim(self):
        self.assertEqual(self.deadlock.victims, ["process1f6a2b8c8"])
        self.assertEqual([p.spid for p in self.deadlock.victim_processes], [57])

    def test_resources(self):
        orders, lines = self.deadlock.resources
        self.assertEqual(orders.kind, "keylock")
        self.assertEqual(orders.object_name, "Sales.dbo.Orders")
        self.assertEqual(orders.index_name, "PK_Orders")
        self.assertEqual(orders.mode, "X")
        self.assertEqual(lines.object_name, "Sales.dbo.OrderLines")

    def test_owners_and_waiters(self):
        orders = self.deadlock.resources[0]
        self.assertEqual([(l.process_id, l.mode) for l in orders.owners], [("process1f6a2b8c8", "X")])
        self.assertEqual([(l.process_id, l.mode, l.request_type) for l in orders.waiters],
                         [("process1f6a2c4e8", "U", "wait")])

    def test_process_lookup(self):
        self.assertEqual(self.deadlock.process("process1f6a2c4e8").spid, 62)
        self.assertIsNone(self.deadlock.process("nope"))


if __name__ == "__main__":
    unittest.main()
