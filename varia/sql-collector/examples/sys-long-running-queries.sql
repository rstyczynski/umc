select * from
(
  select
     opname,
     start_time,
     target,
     sofar,
     totalwork,
     units,
     elapsed_seconds,
     message
   from
        v$session_longops
  order by start_time desc
)
where rownum <=1;