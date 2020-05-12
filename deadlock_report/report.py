"""Plain text deadlock report."""
from .analysis import find_cycle
from .lockmodes import describe
from .waitresource import decode


def _label(process):
    return "spid {}".format(process.spid) if process.ecid == 0 else "spid {} ecid {}".format(process.spid, process.ecid)


def render_process(deadlock, process):
    victim = "  VICTIM" if process.id in deadlock.victims else ""
    lines = ["* {}{}  db {}  login {}  host {}  app {}".format(
        _label(process), victim, process.database, process.login, process.host, process.app or "-")]
    lines.append("    isolation: {}   transaction: {} (trancount {})".format(
        process.isolation_level, process.transaction, process.trancount))
    if process.wait_resource:
        lines.append("    waiting {} ms for {} lock on {}".format(
            process.wait_time_ms, describe(process.lock_mode), process.wait_resource))
        lines.append("        i.e. {}".format(decode(process.wait_resource)))
    if process.procedure:
        lines.append("    procedure: {}".format(process.procedure))
    if process.statement:
        lines.append("    statement: {}".format(process.statement))
    return lines


def _who(deadlock, locks):
    names = []
    for lock in locks:
        process = deadlock.process(lock.process_id)
        names.append("{} ({})".format(_label(process), lock.mode) if process else lock.process_id)
    return ", ".join(names) or "-"


def render_resource(deadlock, resource):
    if resource.kind == "exchangeEvent":
        return render_exchange(deadlock, resource)
    name = resource.object_name
    if resource.index_name:
        name += " / " + resource.index_name
    lines = ["* {} on {}".format(resource.kind, name or resource.id)]
    if resource.mode:
        lines.append("    mode:       {}".format(describe(resource.mode)))
    lines.append("    held by:    {}".format(_who(deadlock, resource.owners)))
    lines.append("    requested:  {}".format(_who(deadlock, resource.waiters)))
    return lines


def render_exchange(deadlock, resource):
    attrs = resource.attributes
    lines = ["* parallel exchange {} at plan node {} ({})".format(
        resource.id, attrs.get("nodeId", "?"), attrs.get("WaitType", "?"))]
    lines.append("    producer:   {}".format(_who(deadlock, resource.owners)))
    lines.append("    waiting:    {}".format(_who(deadlock, resource.waiters)))
    return lines


def render_text(deadlock, number=1, total=1):
    title = "Deadlock {} of {}".format(number, total)
    if deadlock.timestamp:
        title += "  ({})".format(deadlock.timestamp.replace("T", " ").rstrip("Z") + " UTC")
    lines = [title, "=" * len(title)]
    victims = ", ".join(_label(p) for p in deadlock.victim_processes) or "unknown"
    lines.append("Victim (rolled back): {}".format(victims))
    if deadlock.is_parallel:
        lines.append("Type: intra-query parallelism deadlock (threads of one query wait on each other, no other session is involved)")
    cycle = find_cycle(deadlock)
    if cycle:
        names = [_label(deadlock.process(pid)) for pid in cycle]
        lines.append("Cycle: " + " waits for ".join(names + names[:1]))
    lines.append("")
    lines.append("Processes")
    lines.append("---------")
    for process in deadlock.processes:
        lines.extend(render_process(deadlock, process))
    lines.append("")
    lines.append("Resources")
    lines.append("---------")
    for resource in deadlock.resources:
        lines.extend(render_resource(deadlock, resource))
    return "\n".join(lines)


def render_all(deadlocks):
    return "\n\n".join(render_text(d, i, len(deadlocks)) for i, d in enumerate(deadlocks, 1))
