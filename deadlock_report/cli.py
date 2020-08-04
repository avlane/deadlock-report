"""Command line interface: python3 -m deadlock_report FILE..."""
import argparse
import sys

from .parser import parse_deadlocks
from .report import render_all


def read_xml_text(data):
    """Decode a file's bytes. SSMS and sqlcmd may save UTF-8 (with or without BOM) or UTF-16."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8")
    if b"\x00" in data[:4]:  # UTF-16 without a BOM: ASCII characters alternate with NUL bytes
        return data.decode("utf-16-be" if data[0] == 0 else "utf-16-le")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def load_deadlocks(paths, stdin=None):
    """Parse every path ('-' means standard input) and return all deadlocks found."""
    deadlocks = []
    for path in paths:
        if path == "-":
            data = (stdin or sys.stdin.buffer).read()
        else:
            with open(path, "rb") as f:
                data = f.read()
        deadlocks.extend(parse_deadlocks(read_xml_text(data)))
    return deadlocks


def main(argv=None, stdout=None, stdin=None):
    stdout = stdout or sys.stdout
    parser = argparse.ArgumentParser(prog="deadlock_report", description="Explain SQL Server deadlock graphs.")
    parser.add_argument("files", nargs="+", metavar="FILE",
                        help="a .xdl or .xml file containing deadlock graphs, or - to read standard input")
    parser.add_argument("--max-statement-length", type=int, default=0, metavar="N",
                        help="cut statements longer than N characters (default: show them whole)")
    args = parser.parse_args(argv)

    deadlocks = load_deadlocks(args.files, stdin)
    if not deadlocks:
        print("deadlock_report: no deadlock graphs found", file=sys.stderr)
        return 1
    print(render_all(deadlocks, args.max_statement_length), file=stdout)
    return 0
