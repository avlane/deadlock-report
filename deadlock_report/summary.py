"""Summaries across many deadlocks."""
from collections import Counter


def summarize(deadlocks):
    """Count what keeps showing up: objects, victim procedures and applications."""
    objects, victims, apps, hours = Counter(), Counter(), Counter(), Counter()
    parallel = 0
    for deadlock in deadlocks:
        if deadlock.timestamp:
            hours[deadlock.timestamp[:13].replace("T", " ") + ":00"] += 1
        if deadlock.is_parallel:
            parallel += 1
        for name in sorted({r.object_name for r in deadlock.resources if r.object_name}):
            objects[name] += 1
        for process in deadlock.victim_processes:
            victims[process.procedure or "(ad hoc batch)"] += 1
        for app in sorted({p.app for p in deadlock.processes if p.app}):
            apps[app] += 1
    return {
        "total": len(deadlocks),
        "parallel": parallel,
        "objects": objects.most_common(),
        "victims": victims.most_common(),
        "apps": apps.most_common(),
        "hours": sorted(hours.items()),
    }


def render_summary(summary, top=5):
    lines = ["{} deadlock(s), {} of them intra-query parallelism".format(summary["total"], summary["parallel"])]
    for title, key in (("Objects involved", "objects"), ("Victim procedures", "victims"), ("Applications", "apps"),
                       ("By hour (UTC)", "hours")):
        lines.append("")
        lines.append(title)
        shown = summary[key] if key == "hours" else summary[key][:top]
        for name, count in shown:
            lines.append("  {:>3}  {}".format(count, name))
        if not summary[key]:
            lines.append("   -")
    return "\n".join(lines)
