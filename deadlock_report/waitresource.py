"""Decode the waitresource strings found in deadlock graphs and blocked-process reports."""
import re

_KEY = re.compile(r"^KEY:\s*(\d+):(\d+)\s*\(([0-9a-fA-F]+)\)$")
_PAGE = re.compile(r"^PAGE:\s*(\d+):(\d+):(\d+)$")
_RID = re.compile(r"^RID:\s*(\d+):(\d+):(\d+):(\d+)$")
_OBJECT = re.compile(r"^OBJECT:\s*(\d+):(\d+)(?::(\d+))?$")
_EXCHANGE = re.compile(r"^exchangeEvent id=(\S+) WaitType=(\S+) nodeId=(\d+)$")


def decode(wait_resource):
    """Return a short human description, or the original text when the format is not known."""
    text = (wait_resource or "").strip()
    if not text:
        return "nothing (not waiting on a lock)"
    m = _KEY.match(text)
    if m:
        return "key lock {} in HOBT {} of database id {}".format(m.group(3), m.group(2), m.group(1))
    m = _PAGE.match(text)
    if m:
        return "page {} of file {} in database id {}".format(m.group(3), m.group(2), m.group(1))
    m = _RID.match(text)
    if m:
        return "row (RID) slot {} on page {} of file {} in database id {}".format(
            m.group(4), m.group(3), m.group(2), m.group(1))
    m = _OBJECT.match(text)
    if m:
        return "object id {} in database id {}".format(m.group(2), m.group(1))
    m = _EXCHANGE.match(text)
    if m:
        return "parallel exchange {} ({}) at plan node {}".format(m.group(1), m.group(2), m.group(3))
    return text
