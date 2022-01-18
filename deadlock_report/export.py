"""Plain data (for JSON output) from parsed deadlocks."""
import dataclasses
import json

from .analysis import find_cycle


def deadlock_to_dict(deadlock):
    data = dataclasses.asdict(deadlock)
    data["is_parallel"] = deadlock.is_parallel
    data["cycle"] = find_cycle(deadlock)
    for process_data, process in zip(data["processes"], deadlock.processes):
        process_data["statement"] = process.statement
        process_data["procedure"] = process.procedure
    return data


def to_json(deadlocks, indent=2):
    return json.dumps([deadlock_to_dict(d) for d in deadlocks], indent=indent, sort_keys=True)
