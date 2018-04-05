select 
  created_time as TIME, 
  flow as FLOW, 
  count(1) as COUNT_OK, 
  count(err) as COUNT_ERR, 
  Round(min(durati0n),2) as MIN, 
  Round(max(durati0n),2) as MAX, 
  Round(avg(durati0n),2) as AVG 
from (
  select 
    flow, 
    title, 
    to_char(trunc(created_time,'MI'), 'YY-MM-DD HH24:MI') created_time,
    extract(minute from durati0n)*60+extract(second from durati0n) durati0n, 
    err 
  from (
        select * from (
          -- PSO: Process Sales Order
          select 'PSO' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err 
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/ProcessSalesOrderFulfillmentOSMCFSCommsJMSProducer%' and 
                a2.composite_dn like 'default/ProcessSalesOrderFulfillmentSiebelCommsJMSConsumer%' and
                a1.ecid = a2.ecid  
          union all
          select 'PSO' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and 
                a1.composite_dn like 'default/ProcessSalesOrderFulfillmentSiebelCommsJMSConsumer%'
          
          union all
          
          -- SFOBA: Sync Customer
          select 'SFOBA' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err 
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/ProcessFOBillingAccountListRespOSMCFSCommsJMSProducer%' and 
                a2.composite_dn like 'default/ProcessFulfillmentOrderBillingAccountListOSMCFSCommsJMSConsumer%' and
                a1.ecid = a2.ecid  
          union all
          select 'SFOBA' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and 
                a1.composite_dn like 'default/ProcessFulfillmentOrderBillingAccountListOSMCFSCommsJMSConsumer%'
          
          union all
          
          -- BFO: Bill Fullfilment Order
          select 'BFO' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err 
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/ProcessFulfillmentOrderBillingResponseOSMCFSCommsJMSProducer%' and 
                a2.composite_dn like 'default/ProcessFulfillmentOrderBillingOSMCFSCommsJMSConsumer%' and
                a1.ecid = a2.ecid  
          union all
          select 'BFO' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and 
                a1.composite_dn like 'default/ProcessFulfillmentOrderBillingOSMCFSCommsJMSConsumer%'
          
          union all
          
          -- UPDSO: Update Sales Order
          select 'UPDSO' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err 
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/UpdateSalesOrderSiebelCommsProvABCSImpl%' and 
                a2.composite_dn like 'default/UpdateSalesOrderOSMCFSCommsJMSConsumer%' and
                a1.ecid = a2.ecid  
          union all
          select 'UPDSO' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and 
                a1.composite_dn like 'default/UpdateSalesOrderSiebelCommsProvABCSImpl%'            
	        
          union all	
          
          select 'UPDCA-ACNT' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/SyncAccountSiebelAggregatorAdapter%' and
                a2.composite_dn like 'default/SyncCustomerSiebelEventAggregator%' and
                a1.ecid = a2.ecid
          union all
          select 'UPDCA-ACNT' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and
                a1.composite_dn like 'default/SyncAccountSiebelAggregatorAdapter%'
          
          union all
          
          select 'UPDCA-ADDR' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/SyncAddressSiebelAggregatorAdapter%' and
                a2.composite_dn like 'default/SyncCustomerSiebelEventAggregator%' and
                a1.ecid = a2.ecid
          union all
          select 'UPDCA-ADDR' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and
                a1.composite_dn like 'default/SyncAddressSiebelAggregatorAdapter%'
          
          union all
          
          select 'UPDCA-CONT' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/SyncContactSiebelAggregatorAdapter%' and
                a2.composite_dn like 'default/SyncCustomerSiebelEventAggregator%' and
                a1.ecid = a2.ecid
          union all
          select 'UPDCA-CONT' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and
                a1.composite_dn like 'default/SyncContactSiebelAggregatorAdapter%'
          
          union all
          
          select 'UPDCA-BP' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/SyncBPSiebelAggregatorAdapter%' and
                a2.composite_dn like 'default/SyncCustomerSiebelEventAggregator%' and
                a1.ecid = a2.ecid
          union all
          select 'UPDCA-BP' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and
                a1.composite_dn like 'default/SyncBPSiebelAggregatorAdapter%'
          
          union all
          
          select 'UPDCA-EC' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/SyncCustomerPartyListBRMCommsJMSProducer%' and
                a2.composite_dn like 'default/SyncAcctSiebelAggrEventConsumer%' and
                a1.ecid = a2.ecid
          union all
          select 'UPDCA-EC' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and
                a1.composite_dn like 'default/SyncAcctSiebelAggrEventConsumer%'
          union all
          
          select 'UPDCA-BRM' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          from composite_instance a1, composite_instance a2
          where a1.composite_dn like 'default/SyncCustomerPartyListBRMCommsProvABCSImpl%' and
                a2.composite_dn like 'default/SyncCustomerPartyListBRM_01CommsJMSConsumer%' and
                a1.ecid = a2.ecid
          union all
          select 'UPDCA-BRM' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          from composite_instance a1, composite_instance_fault f
          where a1.id = f.composite_instance_id and
                a1.composite_dn like 'default/SyncCustomerPartyListBRM_01CommsJMSConsumer%'
          
          )
        ) 
        where
	  created_time >= trunc(sysdate - 2/1440, 'MI') AND created_time < trunc(sysdate - 1/1440, 'MI') 
          --created_time BETWEEN trunc(sysdate - 2/1440, 'MI') AND trunc(sysdate - 1/1440, 'MI')
) group by flow, created_time
order by created_time;
