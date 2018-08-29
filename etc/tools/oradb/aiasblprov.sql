-- AIA Siebel provider statistics
select created_time as "Time",  R3sult as "Result", flow as "Flow", count(1) as "Count"
from
  (select a1.id, to_char(a1.created_time, 'YY-MM-DD HH24:MI') created_time, a1.state, error_message,
    case
      when a1.state != 32 and a2.error_message is null then 'JTA Timeout'
      when instr(a2.error_message, 'nable to access the following endpoint') > 0 then 'PL Timeout'
      when instr(a2.error_message, 'EAI Siebel Adapte') > 0 then 'EAI Error'
      when instr(a2.error_message, 'Session Token is missing') > 0 then 'Invalid Token'
      when instr(a2.error_message, 'transaction might have timedout or corrupted') > 0 then 'Transaction Timeout'
      when instr(a2.error_message, 'Error on AIASessionPoolManager') > 0 then 'SPM Error'
      when a2.error_message is null then 'OK'
      else 'Other Error'
    end R3sult,
    case
      when instr(a1.composite_dn, 'UpdateSalesOrder') > 0 then 'UPDSO'
      when instr(a1.composite_dn, 'QueryCustomerParty') > 0 then 'SFOBA'
      when instr(a1.composite_dn, 'SyncCustomerSiebelEventAggregator') > 0 then 'UPDCA-EA'
      when instr(a1.composite_dn, 'SyncAcctSiebelAggrEventConsumer') > 0 then 'UPDCA-EC'
      else 'UNKNOWN'
    end Flow
  from __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault a2
  where (a1.composite_dn like 'default/UpdateSalesOrderSiebelCommsProv%' or
         a1.composite_dn like 'default/QueryCustomerPartyListSiebelProv%' or
         a1.composite_dn like 'default/SyncCustomerSiebelEventAggregator%' or
         a1.composite_dn like 'default/SyncAcctSiebelAggrEventConsumer%') and
	 a1.created_time >= trunc(sysdate - 2/1440, 'MI') AND a1.created_time < trunc(sysdate - 1/1440, 'MI') and
         a1.id = a2.composite_instance_id (+)
) group by created_time, flow, R3sult
order by created_time;

