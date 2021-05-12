"""A single-file HTML report."""
from html import escape

from .analysis import find_cycle
from .lockmodes import describe
from .waitresource import decode


def _label(process):
    return "spid {}".format(process.spid) if process.ecid == 0 else "spid {} ecid {}".format(process.spid, process.ecid)


def _td(text, cls=""):
    return '<td{}>{}</td>'.format(' class="{}"'.format(cls) if cls else "", escape(text))


def _who(deadlock, locks):
    parts = []
    for lock in locks:
        process = deadlock.process(lock.process_id)
        parts.append("{} ({})".format(_label(process), lock.mode) if process else lock.process_id)
    return ", ".join(parts) or "-"


def render_deadlock(deadlock, number, total):
    title = "Deadlock {} of {}".format(number, total)
    if deadlock.timestamp:
        title += " at {} UTC".format(deadlock.timestamp.replace("T", " ").rstrip("Z"))
    out = ["<section>", "<h2>{}</h2>".format(escape(title))]
    victims = ", ".join(_label(p) for p in deadlock.victim_processes) or "unknown"
    out.append("<p><strong>Victim (rolled back):</strong> {}</p>".format(escape(victims)))
    cycle = find_cycle(deadlock)
    if cycle:
        names = [_label(deadlock.process(pid)) for pid in cycle]
        out.append("<p><strong>Cycle:</strong> {}</p>".format(escape(" waits for ".join(names + names[:1]))))
    out.append("<h3>Processes</h3>")
    out.append("<table><tr><th>Session</th><th>Database</th><th>Login</th><th>Host</th><th>Application</th>"
               "<th>Waiting for</th><th>Statement</th></tr>")
    for p in deadlock.processes:
        wait = "{} ms for {} on {}".format(p.wait_time_ms, describe(p.lock_mode), decode(p.wait_resource)) if p.wait_resource else "-"
        out.append("<tr>" + _td(_label(p) + (" (victim)" if p.id in deadlock.victims else "")) + _td(p.database)
                   + _td(p.login) + _td(p.host) + _td(p.app or "-") + _td(wait) + _td(p.statement) + "</tr>")
    out.append("</table>")
    out.append("<h3>Resources</h3>")
    out.append("<table><tr><th>Type</th><th>Object</th><th>Mode</th><th>Held by</th><th>Requested by</th></tr>")
    for r in deadlock.resources:
        name = r.object_name + (" / " + r.index_name if r.index_name else "")
        out.append("<tr>" + _td(r.kind) + _td(name or r.id) + _td(describe(r.mode) if r.mode else "-")
                   + _td(_who(deadlock, r.owners)) + _td(_who(deadlock, r.waiters)) + "</tr>")
    out.append("</table>")
    out.append("</section>")
    return "\n".join(out)


def render_html(deadlocks, title="Deadlock report"):
    body = "\n".join(render_deadlock(d, i, len(deadlocks)) for i, d in enumerate(deadlocks, 1))
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<title>{t}</title>\n</head>\n"
            "<body>\n<h1>{t}</h1>\n{b}\n</body>\n</html>\n").format(t=escape(title), b=body)
