# Getting deadlock graphs out of SQL Server

## system_health (nothing to set up)

Every instance since SQL Server 2012 runs the `system_health` Extended Events session, and it records `xml_deadlock_report`.
`sql/get_system_health_deadlocks.sql` has two queries:

1. Reads the `system_health*.xel` files. Use this first: it goes back further and survives restarts.
2. Reads the ring buffer. Quick, but it only keeps recent events and is cleared when the instance restarts.

In SSMS, click the XML in the `xml_report` column, then File > Save As to keep it as an `.xdl` file. Opening an `.xdl` in SSMS shows the graph picture; this tool reads the same file.
To process many at once, right-click the results grid and "Save Results As" CSV is not what you want. Copy the whole column and paste it into a text file; the parser accepts many `<event>` or `<deadlock>` elements one after another.

## Trace flag 1222

On older habits: `DBCC TRACEON (1222, -1)` writes deadlock details to the ERRORLOG as text. That is not the XML this tool reads. Prefer `system_health` and leave the trace flag off unless you need the text in the log.

## Which instance?

Capture on the instance where the deadlock happened. For an availability group, a deadlock on a readable secondary is recorded by that replica.
