"""Work out who waits for whom."""
from typing import Dict, List


def wait_for_edges(deadlock) -> Dict[str, List[str]]:
    """Return {waiting process id: [ids of the processes holding what it wants]}."""
    edges = {}
    for resource in deadlock.resources:
        owners = [o.process_id for o in resource.owners]
        for waiter in resource.waiters:
            for owner in owners:
                if owner != waiter.process_id:
                    targets = edges.setdefault(waiter.process_id, [])
                    if owner not in targets:
                        targets.append(owner)
    return edges


def find_cycle(deadlock) -> List[str]:
    """Return the process ids that form the wait cycle, in wait order, or [] if none is found."""
    edges = wait_for_edges(deadlock)
    order = [p.id for p in deadlock.processes]
    for start in order:
        path = []

        def walk(node):
            if node in path:
                return path[path.index(node):]
            path.append(node)
            for nxt in edges.get(node, []):
                cycle = walk(nxt)
                if cycle:
                    return cycle
            path.pop()
            return None

        cycle = walk(start)
        if cycle:
            # start the cycle at the process that appears first in the graph, for stable output
            first = min(cycle, key=order.index)
            i = cycle.index(first)
            return cycle[i:] + cycle[:i]
    return []
