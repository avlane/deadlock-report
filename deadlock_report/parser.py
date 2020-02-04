"""Parse xml_deadlock_report XML into plain objects."""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def squash(text):
    """Collapse runs of whitespace so a statement fits on one line."""
    return " ".join((text or "").split())


@dataclass
class Frame:
    procname: str = ""
    line: int = 0
    text: str = ""


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
    frames: List[Frame] = field(default_factory=list)
    input_buffer: str = ""

    @property
    def statement(self):
        """The statement that was running: the top stack frame, else the input buffer."""
        if self.frames and self.frames[0].text:
            return self.frames[0].text
        return self.input_buffer

    @property
    def procedure(self):
        """Name of the stored procedure at the top of the stack, or '' for ad hoc batches."""
        if self.frames and self.frames[0].procname not in ("", "adhoc", "unknown"):
            return self.frames[0].procname
        return ""


@dataclass
class Lock:
    """One owner or waiter entry of a resource."""
    process_id: str
    mode: str = ""
    request_type: str = ""


@dataclass
class Resource:
    kind: str  # keylock, pagelock, ridlock, objectlock, exchangeEvent, ...
    id: str = ""
    database_id: int = 0
    object_name: str = ""
    index_name: str = ""
    mode: str = ""
    attributes: dict = field(default_factory=dict)
    owners: List[Lock] = field(default_factory=list)
    waiters: List[Lock] = field(default_factory=list)


@dataclass
class Deadlock:
    processes: List[Process] = field(default_factory=list)
    victims: List[str] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)

    def process(self, process_id):
        for p in self.processes:
            if p.id == process_id:
                return p
        return None

    @property
    def victim_processes(self):
        return [p for p in self.processes if p.id in self.victims]


def parse_frame(el):
    return Frame(procname=el.get("procname", ""), line=_int(el.get("line")), text=squash(el.text))


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
        frames=[parse_frame(f) for f in el.find("executionStack").findall("frame")],
        input_buffer=squash(el.findtext("inputbuf")),
    )


def parse_locks(parent, list_tag, item_tag):
    locks = []
    for item in parent.findall("./{}/{}".format(list_tag, item_tag)):
        locks.append(Lock(item.get("id", ""), item.get("mode", ""), item.get("requestType", "")))
    return locks


def parse_resource(el):
    return Resource(
        kind=el.tag,
        id=el.get("id", ""),
        database_id=_int(el.get("dbid")),
        object_name=el.get("objectname", ""),
        index_name=el.get("indexname", ""),
        mode=el.get("mode", ""),
        attributes={k: v for k, v in el.attrib.items()},
        owners=parse_locks(el, "owner-list", "owner"),
        waiters=parse_locks(el, "waiter-list", "waiter"),
    )


def parse_deadlock(xml_text):
    """Parse a document whose root is a <deadlock> element."""
    root = ET.fromstring(xml_text)
    deadlock = root if root.tag == "deadlock" else root.find(".//deadlock")
    if deadlock is None:
        raise ValueError("no <deadlock> element found")
    return Deadlock(
        processes=[parse_process(p) for p in deadlock.findall("./process-list/process")],
        victims=[v.get("id", "") for v in deadlock.findall("./victim-list/victimProcess")],
        resources=[parse_resource(res) for res in deadlock.findall("./resource-list/*")],
    )
