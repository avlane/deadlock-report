import os
import unittest

from deadlock_report.parser import parse_deadlock, parse_deadlocks

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


class DocumentShapeTests(unittest.TestCase):
    def test_bare_xdl_has_no_timestamp(self):
        self.assertEqual(parse_deadlock(fixture("deadlock_key.xdl")).timestamp, "")

    def test_event_carries_a_timestamp(self):
        self.assertEqual(parse_deadlock(fixture("deadlock_key.xml")).timestamp, "2020-01-14T10:22:31.123Z")

    def test_ring_buffer_has_two_deadlocks_in_order(self):
        found = parse_deadlocks(fixture("ring_buffer.xml"))
        self.assertEqual([d.timestamp for d in found], ["2020-05-02T09:02:14.310Z", "2020-05-02T11:30:05.020Z"])
        self.assertEqual([len(d.processes) for d in found], [3, 2])

    def test_several_events_pasted_together(self):
        text = fixture("deadlock_key.xml") + fixture("deadlock_three_way.xml")
        self.assertEqual(len(parse_deadlocks(text)), 2)

    def test_xml_declaration_and_bom_are_tolerated(self):
        text = "\ufeff<?xml version=\"1.0\" encoding=\"utf-8\"?>\n" + fixture("deadlock_key.xdl")
        self.assertEqual(len(parse_deadlocks(text)), 1)

    def test_deadlock_list_root(self):
        found = parse_deadlocks(fixture("deadlock_list_2008.xdl"))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].victims, ["processa1"])
        self.assertEqual(found[0].resources[0].waiters[0].process_id, "processa2")

    def test_nothing_found(self):
        self.assertEqual(parse_deadlocks("<event/>"), [])


class ParallelTests(unittest.TestCase):
    def setUp(self):
        self.deadlock = parse_deadlock(fixture("deadlock_parallel.xml"))

    def test_is_parallel(self):
        self.assertTrue(self.deadlock.is_parallel)
        self.assertFalse(parse_deadlock(fixture("deadlock_key.xml")).is_parallel)

    def test_threads_share_a_spid(self):
        self.assertEqual({p.spid for p in self.deadlock.processes}, {71})
        self.assertEqual([p.ecid for p in self.deadlock.processes], [0, 2, 4])

    def test_exchange_resources(self):
        pipe = self.deadlock.resources[0]
        self.assertEqual(pipe.kind, "exchangeEvent")
        self.assertEqual(pipe.attributes["WaitType"], "e_waitPipeNewRow")
        self.assertEqual(pipe.waiters[0].process_id, "process1c01a5528")


class MissingPartsTests(unittest.TestCase):
    def test_process_without_execution_stack(self):
        d = parse_deadlock(fixture("deadlock_no_stack.xml"))
        quiet = d.process("process1f6a2c4e8")
        self.assertEqual(quiet.frames, [])
        self.assertEqual(quiet.statement, "")
        self.assertEqual(quiet.procedure, "")
        self.assertEqual(quiet.login, "NT AUTHORITY\\SYSTEM")


class StatementTests(unittest.TestCase):
    def setUp(self):
        self.deadlock = parse_deadlock(fixture("deadlock_key.xdl"))

    def test_frames(self):
        frames = self.deadlock.processes[0].frames
        self.assertEqual([f.procname for f in frames], ["Sales.dbo.usp_UpdateOrderStatus", "adhoc"])
        self.assertEqual(frames[0].line, 31)

    def test_statement_is_the_top_frame_on_one_line(self):
        p = self.deadlock.processes[0]
        self.assertEqual(p.statement, "UPDATE dbo.OrderLines SET Status = @Status WHERE OrderID = @OrderID AND Status <> @Status")

    def test_input_buffer(self):
        self.assertEqual(self.deadlock.processes[1].input_buffer,
                         "EXEC dbo.usp_AddOrderLine @OrderID = 1042, @ProductID = 77, @Qty = 2")

    def test_procedure_name(self):
        self.assertEqual(self.deadlock.processes[1].procedure, "Sales.dbo.usp_AddOrderLine")


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
