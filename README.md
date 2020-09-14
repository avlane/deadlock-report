# deadlock-report

Turns the `xml_deadlock_report` XML that SQL Server writes to the `system_health` Extended Events session into a report you can read without squinting at XML.

Work in progress. `sql/get_system_health_deadlocks.sql` shows how to pull the XML out of the server.

## Usage

```
python3 -m deadlock_report path/to/deadlock.xdl
python3 -m deadlock_report ring_buffer_dump.xml --max-statement-length 120
cat saved.xdl | python3 -m deadlock_report -
```

Input can be a bare `<deadlock>` (an `.xdl` file saved from SSMS), a single `xml_deadlock_report` event, or a ring buffer dump containing many events. Needs Python 3.7 or newer and nothing else.

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
```

## Tests

```
python3 -m unittest discover
```