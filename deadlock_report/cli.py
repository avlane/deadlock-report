"""Command line interface: python3 -m deadlock_report FILE..."""
import argparse
import sys

from .parser import parse_deadlocks
from .report import render_all


def main(argv=None, stdout=None):
    stdout = stdout or sys.stdout
    parser = argparse.ArgumentParser(prog="deadlock_report", description="Explain SQL Server deadlock graphs.")
    parser.add_argument("files", nargs="+", metavar="FILE", help="a .xdl or .xml file containing a deadlock graph")
    parser.add_argument("--max-statement-length", type=int, default=0, metavar="N",
                        help="cut statements longer than N characters (default: show them whole)")
    args = parser.parse_args(argv)

    deadlocks = []
    for path in args.files:
        with open(path, encoding="utf-8") as f:
            deadlocks.extend(parse_deadlocks(f.read()))
    print(render_all(deadlocks, args.max_statement_length), file=stdout)
    return 0
