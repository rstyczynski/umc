-- AIA BRM providers statistics
SELECT 
  created_time as "Time", 
  R3sult as "Result", 
  flow as "Flow", 
  count(1) as "Count"
FROM (
    SELECT 
        to_char(created_time, 'YY-MM-DD HH24:MI') created_time, 
        flow,
        CASE
          WHEN brm_code is NULL AND error_message is NULL THEN 'OK'
          WHEN brm_code IS NOT NULL THEN brm_code
          ELSE 'OTHER ERROR'
        END R3sult
    FROM (
        SELECT 
            a1.id, 
            a11.flow,
            a1.created_time,
            cast(REGEXP_SUBSTR(a2.error_message, 'ErrMsg=([_0-9a-zA-Z]+)',1,1,'i',1) as VARCHAR(30)) brm_code,
            a2.error_message
        FROM 
            (SELECT 
                ecid,
                CASE
                  WHEN cdns='ProcessFulfillmentOrderBillingAccountListOSMCFSCommsJMSConsumer, SyncCustomerPartyListBRMCommsProvABCSImpl' THEN 'SFOBA-L1'
                  WHEN cdns='ProcessFulfillmentOrderBillingOSMCFSCommsJMSConsumer, ProcessFulfillmentOrderBillingBRMCommsProvABCSImpl' THEN 'BFO'
                  WHEN cdns='SyncCustomerPartyListBRM_01CommsJMSConsumer, SyncCustomerPartyListBRMCommsProvABCSImpl' THEN 'UPDCA-L3'         
                  ELSE 'UNKNOWN'
                END Flow
            FROM (
                SELECT 
                    ci.ecid ecid, 
                    LISTAGG(REGEXP_SUBSTR(ci.composite_dn, 'default/(.*)!',1,1,'i',1), ', ') WITHIN GROUP (ORDER BY created_time) "CDNS"
                FROM 
                    PRFMX_SOAINFRA.composite_instance ci
                WHERE 
                    (ci.composite_dn LIKE 'default/ProcessFulfillmentOrderBillingAccountListOSMCFSCommsJMSConsumer%' OR
                     ci.composite_dn LIKE 'default/SyncCustomerPartyListBRM_01CommsJMSConsumer%' OR
                     ci.composite_dn LIKE 'default/SyncCustomerPartyListBRMCommsProv%' OR
                     ci.composite_dn LIKE 'default/ProcessFulfillmentOrderBillingOSMCFSCommsJMSConsumer%' OR
                     ci.composite_dn LIKE 'default/ProcessFulfillmentOrderBillingBRMCommsProv%')
                GROUP BY
                    ci.ecid
            )    
            WHERE
                instr(cdns, 'SyncCustomerPartyListBRMCommsProv') > 0 or 
                instr(cdns, 'ProcessFulfillmentOrderBillingBRMCommsProv') > 0) a11,
            PRFMX_SOAINFRA.composite_instance a1,
            PRFMX_SOAINFRA.composite_instance_fault a2
        WHERE
            a1.ecid = a11.ecid AND
            a1.ecid = a2.ecid (+) AND
            (a1.composite_dn like 'default/SyncCustomerPartyListBRMCommsProv%' OR
             a1.composite_dn like 'default/ProcessFulfillmentOrderBillingBRMCommsProv%')    
    )
    WHERE
        created_time >= trunc(sysdate - 2/1440, 'MI') AND created_time < trunc(sysdate - 1/1440, 'MI')
        --created_time BETWEEN to_date('21-03-2018 14:05:00', 'DD-MM-YYYY HH24:MI:SS') AND to_date('21-03-2018 14:10:00', 'DD-MM-YYYY HH24:MI:SS')
) 
GROUP BY
    created_time, R3sult, flow;

