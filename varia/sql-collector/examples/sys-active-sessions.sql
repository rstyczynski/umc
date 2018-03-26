-- SQL queries running in the system
SELECT a.sid, a.serial#, b.sql_text
FROM v$session a, v$sqlarea b
WHERE a.sql_address=b.address
