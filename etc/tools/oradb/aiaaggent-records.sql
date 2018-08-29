-- Number of records processed in a batch from AIA_AGGREGATED_ENTITIES table
-- the records are processed in a single transaction and need to finish within JTA timeout
-- if they are not finished, they remanin in running state (mediator_state=8)
-- the script selects all instances that were supposed to finished by JTA timeout, i.e. at most 6 minutes ago
-- it should be run every 2 minutes (see time condition on sysdate for details)
select 
  to_char(first_time, 'YY-MM-DD HH24:MI:SS.FF') as "Time", 
  to_char(first_time, 'TZR') as "Timezone",
  case 
    when mediator_state = 8 then 'STUCK' 
    when mediator_state = 4 then 'ERROR-RUN' 
    when mediator_state != 0 then 'ERROR-OTHER' 
    else 'SUCCESS' 
  end "Result", BATCH_SIZE "NumRecords"
from (
  select 
    batch_id, min(id) first_cid, min(created_time) first_time, max(created_time) last_time, mediator_state, count(1) batch_size
  from (
    select a1.id, REGEXP_SUBSTR(a1.conversation_id, '.+\%(.+)',1,1,'i',1) batch_id, 
    a1.created_time, mi.component_state mediator_state, a2.composite_instance_id, a2.error_message, a2.stack_trace 
    from composite_instance a1, composite_instance_fault a2, mediator_instance mi
    where a1.composite_dn like 'default/SyncAcctSiebelAggrEventConsumer%' and 
          a1.id = a2.composite_instance_id (+) and
          a1.id = mi.composite_instance_id (+) and mi.component_state is not null and 
          a1.created_time < sysdate - (6/1440) and a1.created_time > sysdate - (8/1440))
  group by batch_id, mediator_state
  order by min(created_time) desc
);
