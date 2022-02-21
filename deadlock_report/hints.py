"""Rule-of-thumb suggestions. They point at where to look; they are not a diagnosis."""
from .lockmodes import is_read


def suggest(deadlock):
    hints = []
    if deadlock.is_parallel:
        hints.append("Intra-query parallelism deadlock: look at the plan of the victim's query. Updating statistics, "
                     "adding a supporting index or OPTION (MAXDOP 1) on that query are the usual remedies.")
        return hints

    waiters = [(r, w) for r in deadlock.resources for w in r.waiters]
    readers_blocked = [(r, w) for r, w in waiters if is_read(w.mode) and r.kind in ("keylock", "pagelock", "ridlock")]
    if readers_blocked:
        levels = {deadlock.process(w.process_id).isolation_level for _, w in readers_blocked if deadlock.process(w.process_id)}
        if any(level.startswith("read committed") for level in levels):
            hints.append("A reader waits on a writer under READ COMMITTED. READ_COMMITTED_SNAPSHOT on the database "
                         "(or SNAPSHOT isolation) removes shared locks from this pattern.")

    objects = []
    for resource in deadlock.resources:
        if resource.object_name and resource.object_name not in objects:
            objects.append(resource.object_name)
    if len(objects) >= 2 and len(deadlock.processes) >= 2:
        hints.append("The sessions take locks on {} in opposite orders. Making every code path touch the tables in the "
                     "same order prevents this cycle.".format(" and ".join(objects[:3])))

    procs = [p.procedure for p in deadlock.processes if p.procedure]
    if len(procs) >= 2 and len(set(procs)) == 1:
        hints.append("Both sides run {}. Two calls on the same rows deadlock when the procedure reads then writes; "
                     "consider UPDLOCK on the first read or a shorter transaction.".format(procs[0]))

    if any(r.kind in ("pagelock", "objectlock") for r in deadlock.resources):
        hints.append("Page or object level locks suggest scans or lock escalation. A better index on the filtered "
                     "columns often brings this back to row locks.")
    if any(r.kind == "ridlock" for r in deadlock.resources):
        hints.append("RID locks mean the table is a heap. A clustered index gives these updates a better path.")
    if any(p.trancount > 1 for p in deadlock.processes):
        hints.append("A session has trancount above 1, so a transaction is nested or left open. Check that callers "
                     "commit promptly.")
    return hints
