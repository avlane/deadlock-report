"""Names for SQL Server lock modes as they appear in a deadlock graph."""

MODES = {
    "S": "Shared",
    "U": "Update",
    "X": "Exclusive",
    "IS": "Intent Shared",
    "IU": "Intent Update",
    "IX": "Intent Exclusive",
    "SIU": "Shared Intent Update",
    "SIX": "Shared Intent Exclusive",
    "UIX": "Update Intent Exclusive",
    "Sch-S": "Schema Stability",
    "Sch-M": "Schema Modification",
    "BU": "Bulk Update",
    "RangeS-S": "Shared Key-Range and Shared Resource",
    "RangeS-U": "Shared Key-Range and Update Resource",
    "RangeI-N": "Insert Key-Range and Null Resource",
    "RangeI-S": "Insert Key-Range and Shared Resource",
    "RangeI-U": "Insert Key-Range and Update Resource",
    "RangeI-X": "Insert Key-Range and Exclusive Resource",
    "RangeX-S": "Exclusive Key-Range and Shared Resource",
    "RangeX-U": "Exclusive Key-Range and Update Resource",
    "RangeX-X": "Exclusive Key-Range and Exclusive Resource",
}

# modes a plain SELECT takes under READ COMMITTED without row versioning
READ_MODES = frozenset(["S", "IS", "RangeS-S"])


def describe(mode: str) -> str:
    """'IX' -> 'IX (Intent Exclusive)'. Unknown modes are returned unchanged."""
    name = MODES.get(mode)
    return "{} ({})".format(mode, name) if name else mode


def is_read(mode: str) -> bool:
    return mode in READ_MODES
