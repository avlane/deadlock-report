import unittest

from deadlock_report.lockmodes import describe, is_read


class LockModeTests(unittest.TestCase):
    def test_known_modes(self):
        self.assertEqual(describe("IX"), "IX (Intent Exclusive)")
        self.assertEqual(describe("Sch-M"), "Sch-M (Schema Modification)")
        self.assertEqual(describe("RangeS-U"), "RangeS-U (Shared Key-Range and Update Resource)")

    def test_unknown_mode_is_unchanged(self):
        self.assertEqual(describe("ZZ"), "ZZ")
        self.assertEqual(describe(""), "")

    def test_is_read(self):
        self.assertTrue(is_read("S"))
        self.assertFalse(is_read("U"))


if __name__ == "__main__":
    unittest.main()
