import unittest

from deadlock_report.waitresource import decode


class DecodeTests(unittest.TestCase):
    def test_key(self):
        self.assertEqual(decode("KEY: 5:72057594043432960 (8194443284a0)"),
                         "key lock 8194443284a0 in HOBT 72057594043432960 of database id 5")

    def test_page(self):
        self.assertEqual(decode("PAGE: 7:1:2346"), "page 2346 of file 1 in database id 7")

    def test_rid(self):
        self.assertEqual(decode("RID: 11:1:2200:3"), "row (RID) slot 3 on page 2200 of file 1 in database id 11")

    def test_object(self):
        self.assertEqual(decode("OBJECT: 5:1205579333:0"), "object id 1205579333 in database id 5")
        self.assertEqual(decode("OBJECT: 5:1205579333"), "object id 1205579333 in database id 5")

    def test_exchange(self):
        text = "exchangeEvent id=Pipe1b2c3d4e0 WaitType=e_waitPipeNewRow nodeId=3"
        self.assertEqual(decode(text), "parallel exchange Pipe1b2c3d4e0 (e_waitPipeNewRow) at plan node 3")

    def test_unknown_and_empty(self):
        self.assertEqual(decode("METADATA: 5:xyz"), "METADATA: 5:xyz")
        self.assertEqual(decode(""), "nothing (not waiting on a lock)")


if __name__ == "__main__":
    unittest.main()
