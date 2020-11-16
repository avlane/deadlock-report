import io
import os
import unittest

from deadlock_report import cli

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def path(name):
    return os.path.join(FIXTURES, name)


def raw(name):
    with open(path(name), "rb") as f:
        return f.read()


class ReadTextTests(unittest.TestCase):
    def test_utf8(self):
        self.assertEqual(cli.read_xml_text("<a>é</a>".encode("utf-8")), "<a>é</a>")

    def test_utf8_bom(self):
        self.assertEqual(cli.read_xml_text(b"\xef\xbb\xbf<a/>"), "<a/>")

    def test_utf16_with_bom(self):
        self.assertEqual(cli.read_xml_text("<a/>".encode("utf-16")), "<a/>")

    def test_utf16_without_bom(self):
        self.assertEqual(cli.read_xml_text("<a/>".encode("utf-16-le")), "<a/>")


class MainTests(unittest.TestCase):
    def run_main(self, *argv, stdin=None):
        out = io.StringIO()
        code = cli.main(list(argv), out, stdin)
        return code, out.getvalue()

    def test_single_file(self):
        code, out = self.run_main(path("deadlock_key.xml"))
        self.assertEqual(code, 0)
        self.assertIn("Deadlock 1 of 1", out)

    def test_multiple_files_are_numbered_together(self):
        code, out = self.run_main(path("deadlock_key.xml"), path("ring_buffer.xml"))
        self.assertIn("Deadlock 3 of 3", out)

    def test_summary_option(self):
        code, out = self.run_main("--summary", path("ring_buffer.xml"), path("deadlock_key.xml"))
        self.assertEqual(code, 0)
        self.assertIn("3 deadlock(s)", out)
        self.assertNotIn("Processes", out)

    def test_stdin(self):
        code, out = self.run_main("-", stdin=io.BytesIO(raw("deadlock_page.xml")))
        self.assertIn("pagelock on Audit.dbo.AuditLog", out)

    def test_utf16_xdl_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "saved.xdl")
            with open(target, "wb") as f:
                f.write(raw("deadlock_key.xdl").decode("utf-8").encode("utf-16"))
            code, out = self.run_main(target)
        self.assertEqual(code, 0)
        self.assertIn("spid 57  VICTIM", out)

    def test_file_without_deadlocks(self):
        code, out = self.run_main("-", stdin=io.BytesIO(b"<event/>"))
        self.assertEqual(code, 1)
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
