-- select all flows finished in a minute two minutes from now
-- a flow in SOA infra is defined as a set of composites with the same ECID, possibly 
-- running in a single thread in SOA.
SELECT * 
FROM (
	SELECT 
		min(created_time) created_time,
		count(1) cnt_ok, 
		round(min(durat1on),3) mintime, 
		round(max(durat1on),3) maxtime, 
		round(avg(durat1on),3) avgtime, 
		ora_hash(cdns) flow_id, 
		cdns 
	FROM (
		SELECT 
			min(created_time) created_time,
			ecid,
			extract(minute from (max(created_time)-min(created_time)))*60+
			extract(second from (max(created_time)-min(created_time))) durat1on,
			LISTAGG(cdn, ', ') WITHIN GROUP (ORDER BY created_time) "CDNS"
		FROM (
			SELECT 
				ci.ecid ecid, 
				REGEXP_SUBSTR(ci.composite_dn, 'default/(.*)!',1,1,'i',1) cdn, 
				ci.created_time created_time
			FROM 
				__SOAINFRA.composite_instance ci --, PRFMX_SOAINFRA.composite_instance_fault cif
			WHERE 			
				ci.created_time BETWEEN TO_DATE('18-03-21 14:05:00', 'YY-MM-DD HH24:MI:SS') AND
										TO_DATE('18-03-21 14:10:00', 'YY-MM-DD HH24:MI:SS')
		) 
		GROUP BY ecid
	) 
	GROUP BY ora_hash(cdns), cdns
)
ORDER BY created_time;


--SELECT 
--    to_char(trunc(created_time,'MI'), 'YY-MM-DD HH24:MI') time, title, composite_dn 
--FROM  
--    PRFMX_SOAINFRA.composite_instance
--WHERE 
--    rownum < 2;