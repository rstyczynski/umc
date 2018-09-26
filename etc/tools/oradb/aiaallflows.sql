-- AIA all flows statistics
SELECT count(1) as "Count", 
  count(faulted_time) as "CountFaulted",
  round(min(durat1on),3) mintime, round(max(durat1on),3) as "MaxTime", round(avg(durat1on),3) as "AvgTime", 
  percentile_disc(0.5) within group (ORDER BY durat1on ASC) as "p50",
  percentile_disc(0.9) within group (ORDER BY durat1on ASC) as "p90",
  percentile_disc(0.95) within group (ORDER BY durat1on ASC) as "p95",
  min(instance_id) as "SampleCid", NVL(SUBSTR(cdns, 0, INSTR(cdns, ',')-1), cdns) AS as "EntryPoint", cdns as "Cdns"
FROM (
  SELECT ecid, min(instance_id) instance_id,
    extract(minute FROM (max(end_time)-min(created_time)))*60+
    extract(second FROM (max(end_time)-min(created_time))) durat1on,
    LISTAGG(cdn, ', ') WITHIN GROUP (ORDER BY created_time) "CDNS",
    min(created_time) created_time,
    min(faulted_time) faulted_time, max(cui_md) cui_md
  FROM (
    SELECT ci.ecid ecid, ci.id instance_id, 
           REGEXP_SUBSTR(ci.composite_dn, 'default/(.*)!',1,1,'i',1) || ' (' || ri.operation_name || ')' cdn, ci.created_time created_time, 
           greatest(
              nvl(ci.created_time,TO_DATE('18-01-01 00:00:00', 'YY-MM-DD HH24:MI:SS')),
              nvl(ri.created_time,TO_DATE('18-01-01 00:00:00', 'YY-MM-DD HH24:MI:SS')),
              nvl(cui.creation_date,TO_DATE('18-01-01 00:00:00', 'YY-MM-DD HH24:MI:SS')),
              nvl(cui.modify_date,TO_DATE('18-01-01 00:00:00', 'YY-MM-DD HH24:MI:SS'))) end_time, 
           cui.modify_date cui_md,   
           cif.created_time faulted_time, REGEXP_SUBSTR(cif.error_message, 'ErrMsg=([a-zA-Z0-9\-\_]+)',1,1,'i',1) brm_error, cif.error_message 
    FROM __SOAINFRA_SCHEMA__.composite_instance partition (PT_20180606) ci, 
         __SOAINFRA_SCHEMA__.composite_instance_fault partition (PT_20180606) cif, 
         __SOAINFRA_SCHEMA__.reference_instance partition (PT_20180606) ri, 
         __SOAINFRA_SCHEMA__.cube_instance partition (PT_20180605) cui
    WHERE 
         ci.ecid = cif.ecid (+) AND ci.id = ri.composite_instance_id (+) AND ci.id=cui.cmpst_id(+) AND
         ci.created_time BETWEEN TO_DATE('18-06-06 12:35:00', 'YY-MM-DD HH24:MI:SS') AND
                                  TO_DATE('18-06-06 17:20:00', 'YY-MM-DD HH24:MI:SS')
  ) GROUP BY ecid
) GROUP BY ora_hash(cdns), cdns;
