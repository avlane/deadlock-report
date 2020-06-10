import os
import unittest

from deadlock_report.parser import parse_deadlock
from deadlock_report.report import render_text

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return parse_deadlock(f.read())


class TextReportTests(unittest.TestCase):
    def setUp(self):
        self.text = render_text(load("deadlock_key.xdl"))
        self.lines = self.text.splitlines()

    def test_heading_and_victim(self):
        self.assertEqual(self.lines[0], "Deadlock 1 of 1")
        self.assertEqual(self.lines[2], "Victim (rolled back): spid 57")

    def test_timestamp_in_heading(self):
        with open(os.path.join(FIXTURES, "deadlock_key.xml"), encoding="utf-8") as f:
            text = render_text(parse_deadlock(f.read()))
        self.assertEqual(text.splitlines()[0], "Deadlock 1 of 1  (2020-01-14 10:22:31.123 UTC)")

    def test_process_lines(self):
        self.assertIn("* spid 57  VICTIM  db Sales  login CORP\\svc_orders  host APP01  app OrdersWeb", self.lines)
        self.assertIn("* spid 62  db Sales  login CORP\\svc_fulfil  host APP02  app Fulfilment", self.lines)

    def test_wait_and_statement(self):
        self.assertIn("    waiting 4521 ms for U (Update) lock on KEY: 5:72057594043432960 (8194443284a0)", self.lines)
        self.assertIn("    procedure: Sales.dbo.usp_AddOrderLine", self.lines)

    def test_cycle_line(self):
        self.assertIn("Cycle: spid 57 waits for spid 62 waits for spid 57", self.lines)

    def test_three_way_cycle_line(self):
        with open(os.path.join(FIXTURES, "deadlock_three_way.xml"), encoding="utf-8") as f:
            text = render_text(parse_deadlock(f.read()))
        self.assertIn("Cycle: spid 101 waits for spid 104 waits for spid 109 waits for spid 101", text)

    def test_wait_resource_is_decoded(self):
        self.assertIn("        i.e. key lock 8194443284a0 in HOBT 72057594043432960 of database id 5", self.lines)

    def test_page_lock_fixture(self):
        with open(os.path.join(FIXTURES, "deadlock_page.xml"), encoding="utf-8") as f:
            text = render_text(parse_deadlock(f.read()))
        self.assertIn("i.e. page 2346 of file 1 in database id 7", text)
        self.assertIn("* pagelock on Audit.dbo.AuditLog", text)
        self.assertIn("requested:  spid 91 (IX)", text)

    def test_parallel_deadlock(self):
        with open(os.path.join(FIXTURES, "deadlock_parallel.xml"), encoding="utf-8") as f:
            text = render_text(parse_deadlock(f.read()))
        self.assertIn("Type: intra-query parallelism deadlock", text)
        self.assertIn("Victim (rolled back): spid 71 ecid 2", text)
        self.assertIn("* parallel exchange Pipe1b2c3d4e0 at plan node 3 (e_waitPipeNewRow)", text)
        self.assertIn("producer:   spid 71", text)

    def test_process_without_a_statement_is_still_listed(self):
        with open(os.path.join(FIXTURES, "deadlock_no_stack.xml"), encoding="utf-8") as f:
            text = render_text(parse_deadlock(f.read()))
        self.assertIn("* spid 12  db Sales  login NT AUTHORITY\\SYSTEM  host SQLPROD01  app -", text)

    def test_resources(self):
        self.assertIn("* keylock on Sales.dbo.Orders / PK_Orders", self.lines)
        self.assertIn("    mode:       X (Exclusive)", self.lines)
        self.assertIn("    held by:    spid 57 (X)", self.lines)
        self.assertIn("    requested:  spid 62 (U)", self.lines)


if __name__ == "__main__":
    unittest.main()
