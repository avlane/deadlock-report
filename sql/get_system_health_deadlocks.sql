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
