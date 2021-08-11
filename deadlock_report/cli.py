"""Command line interface: python3 -m deadlock_report FILE..."""
import argparse
import sys
import xml.etree.ElementTree as ET

from . import filters
from .parser import parse_deadlocks
from .html_report import render_html
from .report import render_all
from .summary import render_summary, summarize


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
    parser.add_argument("--summary", action="store_true",
                        help="print counts of objects, victim procedures and applications instead of each deadlock")
    parser.add_argument("--db", metavar="NAME", help="only deadlocks that involve this database")
    parser.add_argument("--object", metavar="TEXT", dest="object_name",
                        help="only deadlocks on objects whose name contains TEXT (case-insensitive)")
    parser.add_argument("--format", choices=["text", "html"], default="text", help="output format (default: text)")
    parser.add_argument("-o", "--output", metavar="PATH", help="write the report to a file instead of standard output")
    args = parser.parse_args(argv)

    try:
        deadlocks = load_deadlocks(args.files, stdin)
    except OSError as err:
        print("deadlock_report: {}".format(err), file=sys.stderr)
        return 2
    except ET.ParseError as err:
        print("deadlock_report: the input is not well-formed XML ({})".format(err), file=sys.stderr)
        return 2
    if not deadlocks:
        print("deadlock_report: no deadlock graphs found", file=sys.stderr)
        return 1
    deadlocks = filters.apply(deadlocks, args.db, args.object_name)
    if not deadlocks:
        print("deadlock_report: no deadlocks match the filters", file=sys.stderr)
        return 1
    if args.summary:
        output = render_summary(summarize(deadlocks)) + "\n"
    elif args.format == "html":
        output = render_html(deadlocks)
    else:
        output = render_all(deadlocks, args.max_statement_length) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print("Wrote {} deadlock(s) to {}".format(len(deadlocks), args.output), file=stdout)
    else:
        stdout.write(output)
    return 0
