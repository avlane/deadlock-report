"""Pick the deadlocks you care about."""


def touches_database(deadlock, name):
    name = name.lower()
    if any(p.database.lower() == name for p in deadlock.processes):
        return True
    return any(r.object_name.lower().startswith(name + ".") for r in deadlock.resources)


def touches_object(deadlock, text):
    text = text.lower()
    return any(text in r.object_name.lower() for r in deadlock.resources)


def apply(deadlocks, database=None, object_name=None):
    result = deadlocks
    if database:
        result = [d for d in result if touches_database(d, database)]
    if object_name:
        result = [d for d in result if touches_object(d, object_name)]
    return result
