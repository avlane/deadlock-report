"""Plain text deadlock report."""


def _label(process):
    return "spid {}".format(process.spid) if process.ecid == 0 else "spid {} ecid {}".format(process.spid, process.ecid)


def render_process(deadlock, process):
    victim = "  VICTIM" if process.id in deadlock.victims else ""
    lines = ["* {}{}  db {}  login {}  host {}  app {}".format(
        _label(process), victim, process.database, process.login, process.host, process.app or "-")]
    lines.append("    isolation: {}   transaction: {} (trancount {})".format(
        process.isolation_level, process.transaction, process.trancount))
    if process.wait_resource:
        lines.append("    waiting {} ms for {} on {}".format(process.wait_time_ms, process.lock_mode, process.wait_resource))
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
    name = resource.object_name
    if resource.index_name:
        name += " / " + resource.index_name
    lines = ["* {} on {}".format(resource.kind, name or resource.id)]
    lines.append("    held by:    {}".format(_who(deadlock, resource.owners)))
    lines.append("    requested:  {}".format(_who(deadlock, resource.waiters)))
    return lines


def render_text(deadlock, number=1, total=1):
    title = "Deadlock {} of {}".format(number, total)
    lines = [title, "=" * len(title)]
    victims = ", ".join(_label(p) for p in deadlock.victim_processes) or "unknown"
    lines.append("Victim (rolled back): {}".format(victims))
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
