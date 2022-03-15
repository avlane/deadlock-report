"""A single-file HTML report."""
from html import escape

from .analysis import find_cycle
from .hints import suggest
from .lockmodes import describe
from .waitresource import decode


def _label(process):
    return "spid {}".format(process.spid) if process.ecid == 0 else "spid {} ecid {}".format(process.spid, process.ecid)


STYLE = """
body { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; margin: 2em auto; max-width: 1100px; color: #222; }
h1 { border-bottom: 2px solid #444; padding-bottom: .2em; }
section { margin: 2em 0; padding: 1em 1.5em; border: 1px solid #ccc; border-radius: 6px; }
table { border-collapse: collapse; width: 100%; margin: .5em 0 1em; }
th, td { border: 1px solid #ddd; padding: 4px 8px; text-align: left; vertical-align: top; }
th { background: #f0f0f0; }
tr.victim td { background: #fdecea; }
td.stmt { font-family: Consolas, Menlo, monospace; font-size: 90%; }
.cycle { font-weight: bold; }
"""


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
        out.append('<p class="cycle"><strong>Cycle:</strong> {}</p>'.format(escape(" waits for ".join(names + names[:1]))))
    out.append("<h3>Processes</h3>")
    out.append("<table><tr><th>Session</th><th>Database</th><th>Login</th><th>Host</th><th>Application</th>"
               "<th>Waiting for</th><th>Statement</th></tr>")
    for p in deadlock.processes:
        wait = "{} ms for {} on {}".format(p.wait_time_ms, describe(p.lock_mode), decode(p.wait_resource)) if p.wait_resource else "-"
        row_class = ' class="victim"' if p.id in deadlock.victims else ""
        out.append("<tr{}>".format(row_class) + _td(_label(p) + (" (victim)" if p.id in deadlock.victims else ""))
                   + _td(p.database) + _td(p.login) + _td(p.host) + _td(p.app or "-") + _td(wait)
                   + _td(p.statement, "stmt") + "</tr>")
    out.append("</table>")
    out.append("<h3>Resources</h3>")
    out.append("<table><tr><th>Type</th><th>Object</th><th>Mode</th><th>Held by</th><th>Requested by</th></tr>")
    for r in deadlock.resources:
        name = r.object_name + (" / " + r.index_name if r.index_name else "")
        out.append("<tr>" + _td(r.kind) + _td(name or r.id) + _td(describe(r.mode) if r.mode else "-")
                   + _td(_who(deadlock, r.owners)) + _td(_who(deadlock, r.waiters)) + "</tr>")
    out.append("</table>")
    hints = suggest(deadlock)
    if hints:
        out.append("<h3>Things to check</h3>")
        out.append("<ul>" + "".join("<li>{}</li>".format(escape(h)) for h in hints) + "</ul>")
    batches = [p for p in deadlock.processes if p.input_buffer and p.input_buffer != p.statement]
    if batches:
        out.append("<details><summary>Input buffers</summary>")
        for p in batches:
            out.append("<p>{}: <code>{}</code></p>".format(escape(_label(p)), escape(p.input_buffer)))
        out.append("</details>")
    out.append("</section>")
    return "\n".join(out)


def render_html(deadlocks, title="Deadlock report"):
    body = "\n".join(render_deadlock(d, i, len(deadlocks)) for i, d in enumerate(deadlocks, 1))
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<title>{t}</title>\n<style>{s}</style>\n</head>\n"
            "<body>\n<h1>{t}</h1>\n{b}\n</body>\n</html>\n").format(t=escape(title), b=body, s=STYLE)
