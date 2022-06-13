# deadlock-report

Turns the `xml_deadlock_report` XML that SQL Server writes to the `system_health` Extended Events session into a report you can read without squinting at XML: who the victim was, what each session was running, what they were waiting for, the wait cycle, and a few things to check.

## Usage

```
python3 -m deadlock_report path/to/deadlock.xdl
python3 -m deadlock_report ring_buffer_dump.xml --max-statement-length 120
python3 -m deadlock_report dump.xml --summary
python3 -m deadlock_report dump.xml --format html -o report.html
python3 -m deadlock_report dump.xml --format json --db Sales
cat saved.xdl | python3 -m deadlock_report -
```

| option | what it does |
|---|---|
| `--summary` | counts per object, victim procedure, application and hour instead of each graph |
| `--format text\|html\|json` | output format, text by default |
| `-o PATH` | write to a file |
| `--db NAME`, `--object TEXT` | keep only deadlocks that involve a database or an object name |
| `--max-statement-length N` | cut long statements in the text report |

Input can be a bare `<deadlock>` (an `.xdl` file saved from SSMS), a SQL Server 2008 style `<deadlock-list>`, a single `xml_deadlock_report` event, or a ring buffer dump with many events, in UTF-8 or UTF-16. Graphs are sorted by time.
Intra-query parallelism deadlocks (exchange events) are recognised too.

`docs/capturing.md` explains how to get graphs out of the server and `sql/get_system_health_deadlocks.sql` has the queries.

Needs Python 3.8 or newer and nothing else. `pip install .` also installs a `deadlock-report` command.

### Sample output

```
Deadlock 1 of 1  (2020-01-14 10:22:31.123 UTC)
==============================================
Victim (rolled back): spid 57
Cycle: spid 57 waits for spid 62 waits for spid 57

Processes
---------
* spid 57  VICTIM  db Sales  login CORP\svc_orders  host APP01  app OrdersWeb
    isolation: read committed (2)   transaction: user_transaction (trancount 2)
    waiting 4521 ms for U (Update) lock on KEY: 5:72057594043432960 (8194443284a0)
        i.e. key lock 8194443284a0 in HOBT 72057594043432960 of database id 5
    procedure: Sales.dbo.usp_UpdateOrderStatus
    statement: UPDATE dbo.OrderLines SET Status = @Status WHERE OrderID = @OrderID AND Status <> @Status
...
Things to check
---------------
* The sessions take locks on Sales.dbo.Orders and Sales.dbo.OrderLines in opposite orders. Making every code path touch the tables in the same order prevents this cycle.
```

The hints are rules of thumb that say where to look, not a diagnosis.

## Tests

```
python3 -m unittest discover
```

The fixtures in `tests/fixtures` are made-up graphs: key lock, page lock, three-way key cycle, RID lock, parallel exchange, a process without an execution stack, and a 2008 style list.