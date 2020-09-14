-- Pull xml_deadlock_report events out of the system_health Extended Events session.
-- Run on the instance that had the deadlock. Needs VIEW SERVER STATE.
-- Save the xml_report column of a row as a .xdl file, or copy the whole column to a .xml file,
-- and feed it to deadlock_report.

-- 1. From the system_health event files (survives restarts, keeps more history)
SELECT  x.event_xml.value('(event/@timestamp)[1]', 'datetime2')  AS event_time_utc,
        x.event_xml.query('(event/data[@name="xml_report"]/value/deadlock)[1]') AS xml_report
FROM (
    SELECT CAST(event_data AS xml) AS event_xml
    FROM sys.fn_xe_file_target_read_file(N'system_health*.xel', NULL, NULL, NULL)
    WHERE object_name = N'xml_deadlock_report'
) AS x
ORDER BY event_time_utc DESC;

-- 2. From the ring buffer (fast, but only holds recent events and is lost on restart)
SELECT  xed.event_xml.value('(@timestamp)[1]', 'datetime2')  AS event_time_utc,
        xed.event_xml.query('(data[@name="xml_report"]/value/deadlock)[1]') AS xml_report
FROM (
    SELECT CAST(st.target_data AS xml) AS target_xml
    FROM sys.dm_xe_session_targets AS st
    JOIN sys.dm_xe_sessions AS s ON s.address = st.event_session_address
    WHERE s.name = N'system_health'
      AND st.target_name = N'ring_buffer'
) AS t
CROSS APPLY t.target_xml.nodes('RingBufferTarget/event[@name="xml_deadlock_report"]') AS xed(event_xml)
ORDER BY event_time_utc DESC;
