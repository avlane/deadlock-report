"""Command line interface: python3 -m deadlock_report FILE..."""
import argparse
import sys

from .parser import parse_deadlock
from .report import render_all


def main(argv=None, stdout=None):
    stdout = stdout or sys.stdout
    parser = argparse.ArgumentParser(prog="deadlock_report", description="Explain SQL Server deadlock graphs.")
    parser.add_argument("files", nargs="+", metavar="FILE", help="a .xdl or .xml file containing a deadlock graph")
    args = parser.parse_args(argv)

    deadlocks = []
    for path in args.files:
        with open(path, encoding="utf-8") as f:
            deadlocks.append(parse_deadlock(f.read()))
    print(render_all(deadlocks), file=stdout)
    return 0
