"""Parse xml_deadlock_report XML into plain objects."""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class Process:
    id: str
    spid: int
    ecid: int = 0
    status: str = ""
    wait_resource: str = ""
    wait_time_ms: int = 0
    lock_mode: str = ""
    isolation_level: str = ""
    login: str = ""
    host: str = ""
    app: str = ""
    database: str = ""
    transaction: str = ""
    trancount: int = 0


@dataclass
class Deadlock:
    processes: List[Process] = field(default_factory=list)


def parse_process(el):
    return Process(
        id=el.get("id", ""),
        spid=_int(el.get("spid")),
        ecid=_int(el.get("ecid")),
        status=el.get("status", ""),
        wait_resource=el.get("waitresource", ""),
        wait_time_ms=_int(el.get("waittime")),
        lock_mode=el.get("lockMode", ""),
        isolation_level=el.get("isolationlevel", ""),
        login=el.get("loginname", ""),
        host=el.get("hostname", ""),
        app=el.get("clientapp", ""),
        database=el.get("currentdbname", ""),
        transaction=el.get("transactionname", ""),
        trancount=_int(el.get("trancount")),
    )


def parse_deadlock(xml_text):
    """Parse a document whose root is a <deadlock> element."""
    root = ET.fromstring(xml_text)
    deadlock = root if root.tag == "deadlock" else root.find(".//deadlock")
    if deadlock is None:
        raise ValueError("no <deadlock> element found")
    return Deadlock(processes=[parse_process(p) for p in deadlock.findall("./process-list/process")])
