-- retrieves metrics for AIA flows (order management, update customer accounts) in the past minute
SELECT 
  created_time as "Time", 
  flow as "Flow", 
  count(1) as "CountOk", 
  count(err) as "CountErr", 
  Round(min(durati0n),2) as "Min", 
  Round(max(durati0n),2) as "Max", 
  Round(avg(durati0n),2) as "Avg" 
FROM (
  SELECT 
    flow, 
    title, 
    to_char(trunc(created_time,'MI'), 'YY-MM-DD HH24:MI') created_time,
    extract(minute FROM durati0n)*60+extract(second FROM durati0n) durati0n, 
    err 
  FROM (
        SELECT * 
        FROM (

          -- Order Management Process Flows
          -- PSO: Process Sales Order
          SELECT 'PSO' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err 
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/ProcessSalesOrderFulfillmentOSMCFSCommsJMSProducer%' AND 
                a2.composite_dn LIKE 'default/ProcessSalesOrderFulfillmentSiebelCommsJMSConsumer%' AND
                a1.ecid = a2.ecid  
          UNION ALL
          SELECT 'PSO' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND 
                a1.composite_dn LIKE 'default/ProcessSalesOrderFulfillmentSiebelCommsJMSConsumer%'
          
          UNION ALL
          
          -- SFOBA: Sync Customer
          SELECT 'SFOBA' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err 
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/ProcessFOBillingAccountListRespOSMCFSCommsJMSProducer%' AND 
                a2.composite_dn LIKE 'default/ProcessFulfillmentOrderBillingAccountListOSMCFSCommsJMSConsumer%' AND
                a1.ecid = a2.ecid  
          UNION ALL
          SELECT 'SFOBA' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND 
                a1.composite_dn LIKE 'default/ProcessFulfillmentOrderBillingAccountListOSMCFSCommsJMSConsumer%'
          
          UNION ALL
          
          -- BFO: Bill Fullfilment Order
          SELECT 'BFO' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err 
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/ProcessFulfillmentOrderBillingResponseOSMCFSCommsJMSProducer%' AND 
                a2.composite_dn LIKE 'default/ProcessFulfillmentOrderBillingOSMCFSCommsJMSConsumer%' AND
                a1.ecid = a2.ecid  
          UNION ALL
          SELECT 'BFO' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND 
                a1.composite_dn LIKE 'default/ProcessFulfillmentOrderBillingOSMCFSCommsJMSConsumer%'
          
          UNION ALL
          
          -- UPDSO: Update Sales Order
          SELECT 'UPDSO' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err 
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/UpdateSalesOrderSiebelCommsProvABCSImpl%' AND 
                a2.composite_dn LIKE 'default/UpdateSalesOrderOSMCFSCommsJMSConsumer%' AND
                a1.ecid = a2.ecid  
          UNION ALL
          SELECT 'UPDSO' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND 
                a1.composite_dn LIKE 'default/UpdateSalesOrderSiebelCommsProvABCSImpl%'            
	        
          UNION ALL	
          
          -- UPDCA: Update Customer Accounts Process Flows
          -- The below SQLs represent UPDCA flow leg 1 (events are inject from Siebel to AIA)
          -- Account events
          SELECT 'UPDCA-ACNT' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/SyncAccountSiebelAggregatorAdapter%' AND
                a2.composite_dn LIKE 'default/SyncCustomerSiebelEventAggregator%' AND
                a1.ecid = a2.ecid
          UNION ALL
          SELECT 'UPDCA-ACNT' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND
                a1.composite_dn LIKE 'default/SyncAccountSiebelAggregatorAdapter%'
          
          UNION ALL
          
          -- Address events
          SELECT 'UPDCA-ADDR' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/SyncAddressSiebelAggregatorAdapter%' AND
                a2.composite_dn LIKE 'default/SyncCustomerSiebelEventAggregator%' AND
                a1.ecid = a2.ecid
          UNION ALL
          SELECT 'UPDCA-ADDR' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND
                a1.composite_dn LIKE 'default/SyncAddressSiebelAggregatorAdapter%'
          
          UNION ALL
          
          -- Contact events
          SELECT 'UPDCA-CONT' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/SyncContactSiebelAggregatorAdapter%' AND
                a2.composite_dn LIKE 'default/SyncCustomerSiebelEventAggregator%' AND
                a1.ecid = a2.ecid
          UNION ALL
          SELECT 'UPDCA-CONT' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND
                a1.composite_dn LIKE 'default/SyncContactSiebelAggregatorAdapter%'
          
          UNION ALL
          
          -- Billing Profile events
          SELECT 'UPDCA-BP' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/SyncBPSiebelAggregatorAdapter%' AND
                a2.composite_dn LIKE 'default/SyncCustomerSiebelEventAggregator%' AND
                a1.ecid = a2.ecid
          UNION ALL
          SELECT 'UPDCA-BP' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND
                a1.composite_dn LIKE 'default/SyncBPSiebelAggregatorAdapter%'
          
          UNION ALL
          
          -- UPDCA flow leg 2 - events are consumed from the AIA_AGGREGATED_ENTITIES table
          -- this is the flow that spans across a reseuqnecer, check resequencer XYZ for additional details 
          -- also check the stats on AIA_AGGREGATED_ENTITIES table
          SELECT 'UPDCA-EC' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/SyncCustomerPartyListBRMCommsJMSProducer%' AND
                a2.composite_dn LIKE 'default/SyncAcctSiebelAggrEventConsumer%' AND
                a1.ecid = a2.ecid
          UNION ALL
          SELECT 'UPDCA-EC' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND
                a1.composite_dn LIKE 'default/SyncAcctSiebelAggrEventConsumer%'
          UNION ALL
          
          -- UPDCA flow leg 3 - the event is consumed from CPARTY Topic and sent over to BRM
          SELECT 'UPDCA-BRM' flow, a1.title, a1.created_time, a1.created_time-a2.created_time durati0n, null err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance a2
          WHERE a1.composite_dn LIKE 'default/SyncCustomerPartyListBRMCommsProvABCSImpl%' AND
                a2.composite_dn LIKE 'default/SyncCustomerPartyListBRM_01CommsJMSConsumer%' AND
                a1.ecid = a2.ecid
          UNION ALL
          SELECT 'UPDCA-BRM' flow, a1.title, a1.created_time, null durati0n, 'ERROR' err
          FROM __SOAINFRA_SCHEMA__.composite_instance a1, __SOAINFRA_SCHEMA__.composite_instance_fault f
          WHERE a1.id = f.composite_instance_id AND
                a1.composite_dn LIKE 'default/SyncCustomerPartyListBRM_01CommsJMSConsumer%'
          
          )
        ) 
        WHERE
	  created_time >= trunc(sysdate - 2/1440, 'MI') AND created_time < trunc(sysdate - 1/1440, 'MI') 
          --created_time BETWEEN to_date('21-03-2018 14:05:00', 'DD-MM-YYYY HH24:MI:SS') AND to_date('21-03-2018 14:10:00', 'DD-MM-YYYY HH24:MI:SS')
) 
GROUP BY flow, created_time
ORDER BY created_time;
