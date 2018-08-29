-- Resequencer container IDs error and locked groups
SELECT 
to_char(sysdate,'YYYY-MM-DD HH24:MI:SS') as "Time",
mg.CONTAINER_ID as "ContainerId",
sum(decode(mg.status, 3, 1, 0)) as "ErrorGroups",
sum(decode(mg.status, 1, 1, 0)) as "LockedGroups"
--date_to_epoch(mgl.renewal_time) as "renewal_time"
FROM __SOAINFRA_SCHEMA__.MEDIATOR_GROUP_STATUS mg, __SOAINFRA_SCHEMA__.MEDIATOR_CONTAINERID_LEASE mgl
where mg.status in (1, 3) and mg.CONTAINER_ID=mgl.CONTAINER_ID(+)
group by mg.CONTAINER_ID, mgl.renewal_time
union
SELECT 
to_char(sysdate,'YYYY-MM-DD HH24:MI:SS') as "Time",
mg2.CONTAINER_ID as "ContainerId",
sum(decode(mg2.status, 3, 1, 0)) as "ErrorGroups",
sum(decode(mg2.status, 1, 1, 0)) as "LockedGroups"
--date_to_epoch(mgl2.renewal_time) as "renewal_time"
FROM __SOAINFRA_SCHEMA__.MEDIATOR_GROUP_STATUS mg2, __SOAINFRA_SCHEMA__.MEDIATOR_CONTAINERID_LEASE mgl2
where  mg2.CONTAINER_ID(+)=mgl2.CONTAINER_ID
group by mg2.CONTAINER_ID, mgl2.renewal_time;

