-- Resequencer statuses
SELECT
	to_char(sysdate,'YYYY-MM-DD HH24:MI:SS') as "Time",
	decode(gs.status, '0','READY','1','LOCKED','3','ERRORED','4','TIMED OUT','6','GROUP ERROR') || '-' ||
	decode(m.status,'0','READY','2','PROCESSED','3','ERRORED','4','TIMED OUT','6','ABORTED') as "GrpMsgStatus",
	gs.status as "GrpStatus",
	m.status as "MsgStatus",
	count(1) as "Count",
	SUBSTR(gs.component_dn,-INSTR(reverse(gs.component_dn),'/') + 1) as "Component",
	gs.container_id
FROM 
	__SOAINFRA_SCHEMA__.mediator_group_status gs, __SOAINFRA_SCHEMA__.mediator_resequencer_message m
WHERE 
	m.owner_id = gs.id and m.group_id = gs.group_id and gs.status <= 3 and m.status <= 3
GROUP BY 
	gs.component_dn, gs.status, m.status, gs.container_id
ORDER BY 
	gs.component_dn, gs.status, gs.container_id;

