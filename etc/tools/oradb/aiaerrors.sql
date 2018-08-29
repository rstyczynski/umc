-- AIA errors per flow
select to_char(max(created_time),'YY-MM-DD HH24:MI') as "Time", flow as "Flow", count(1) as "Count", error_type as "ErrorType" from (
  select flow,
  case
    when error_type is null then 'UNKNOWN_ERROR'
    else error_type
  end error_type, error_message, cid, created_time from
    (select flow, xml_error || brm_error || jca_error || oramed_error || sbl_error || other_error ||
            aia_error || case when brm_error is null then brm_error2 else null end || jms_error error_type,
            error_message, cid, created_time
    from (
      select
        cast(REGEXP_SUBSTR(error_message, '(XML-[0-9]+)',1,1,'i',1) AS VARCHAR(50)) xml_error,
        cast(REGEXP_SUBSTR(error_message, 'ErrMsg=([_0-9a-zA-Z]+)',1,1,'i',1) AS VARCHAR(50)) brm_error,
        cast(REGEXP_SUBSTR(error_message, '(BRM-ERR[_0-9a-zA-Z]+)',1,1,'i',1) AS VARCHAR(50)) brm_error2,
        cast(REGEXP_SUBSTR(error_message, '(JCA-[0-9]+)',1,1,'i',1) AS VARCHAR(50)) jca_error,
        cast(REGEXP_SUBSTR(error_message, '(ORAMED-[0-9]+)',1,1,'i',1) AS VARCHAR(50)) oramed_error,
        cast(REGEXP_SUBSTR(error_message, '(SBL-[A-Z]+-[0-9]+)',1,1,'i',1) AS VARCHAR(50)) sbl_error,
        cast(REGEXP_SUBSTR(error_message, '(AIA_ERR_[_A-Z0-9]+)',1,1,'i',1) AS VARCHAR(50)) aia_error,
        cast(REGEXP_SUBSTR(error_message, '(ERRJMS[_0-9a-zA-Z]+)',1,1,'i',1) AS VARCHAR(50)) jms_error,
        case
          when instr(error_message, 'Unable to access the following endpoint') > 0 then 'HTTP_TIMEOUT'
          when instr(error_message, 'The transaction might have timedout') > 0 then 'JTA_TIMEOUT'
          when instr(error_message, 'The result of from-spec is null') > 0 then 'DATA_ERROR'
          else null
        end other_error,
        case
          when cdn = 'ProcessSalesOrderFulfillmentSiebelCommsReqABCSImpl' then 'PSO-L1'
          when cdn = 'ProcessSalesOrderFulfillmentSiebelCommsJMSConsumer' then 'PSO-L1'
          when cdn = 'ProcessSalesOrderFulfillmentOSMCFSCommsJMSProducer' then 'PSO-L1'
          when cdn = 'ProcessFulfillmentOrderBillingAccountListOSMCFSCommsJMSConsumer' then 'SFOBA-L1'
          when cdn = 'CommsProcessFulfillmentOrderBillingAccountListEBF' then 'SFOBA-L1'
          when cdn = 'CommsProcessBillingAccountListEBF' then 'SFOBA-L1'
          when cdn = 'QueryCustomerPartyListSiebelProvABCSImplV2' then 'SFOBA-L1'
          when cdn = 'SyncCustomerPartyListBRMCommsProvABCSImpl' and title like 'SalesOrder%' then 'SFOBA-L2'
          when cdn = 'CommunicationsCustomerPartyEBSV2Resequencer' then 'SFOBA-L2'
          when cdn = 'ProcessFulfillmentOrderBillingOSMCFSCommsJMSConsumer' then 'BFO-L1'
          when cdn = 'ProcessFulfillmentOrderBillingBRMCommsProvABCSImpl' then 'BFO-L1'
          when cdn = 'ProcessFulfillmentOrderBillingBRMCommsAddSubProcess' then 'BFO-L1'
          when cdn = 'ProcessFulfillmentOrderBillingBRMCommsBPSubProcess' then 'BFO-L1'
          when cdn = 'ProcessFulfillmentOrderBillingBRMCommsDeleteSubProcess' then 'BFO-L1'
          when cdn = 'ProcessFulfillmentOrderBillingBRMCommsTOOSubProcess' then 'BFO-L1'
          when cdn = 'ProcessFulfillmentOrderBillingBRMCommsUpdateSubProcess' then 'BFO-L1'
          when cdn = 'ProcessFulfillmentOrderBillingResponseOSMCFSCommsJMSProducer' then 'BFO-L1'
          when cdn = 'UpdateSalesOrderOSMCFSCommsJMSConsumer' then 'UPDSO-L1'
          when cdn = 'UpdateSalesOrderSiebelCommsProvABCSImpl' then 'UPDSO-L2'
          when cdn = 'SyncCustomerSiebelEventAggregator' then 'UPDCA-L1'
          when cdn = 'SyncAcctSiebelAggrEventConsumer' then 'UPDCA-L2'
          when cdn = 'SyncAccountSiebelReqABCSImpl' then 'UPDCA-L2'
          when cdn = 'SyncCustomerPartyListBRMCommsProvABCSImpl' and title not like 'SalesOrder%' then 'UPDCA-L3'
          when cdn = 'SyncCustomerPartyListBRM_01CommsJMSConsumer' then 'UPDCA-L3'
          when cdn = 'ProcessProvisioningOrderOSMCFSCommsJMSConsumer' then 'COM-SOM-L1'
          when cdn = 'ProcessProvisioningOrderOSMPROVCommsJMSProducer' then 'COM-SOM-L1'
          when cdn = 'ProcessFulfillmentOrderUpdateOSMCFSCommsJMSProducer' then 'COM-SOM-L2'
          when cdn = 'ProcessFulfillmentOrderUpdateOSMPROVCommsJMSConsumer' then 'COM-SOM-L2'
          else concat('UNKNOWN - ', cdn)
        end flow,
        error_message, cid, created_time
      from
        (select t1.cid, ci.title, REGEXP_SUBSTR(ci.composite_dn, 'default/(.*)!',1,1,'i',1) cdn,
               t1.created_time created_time, t2.error_message error_message from
          (select * from (
            select cif.composite_instance_id cid, cif.created_time, cif.ecid,
                row_number() OVER (PARTITION BY cif.ecid ORDER BY cif.created_time) as rn
            from __SOAINFRA_SCHEMA__.composite_instance_fault cif
          )
          where rn = 1) t1,
          (select * from (
            select cif.composite_instance_id cid, cif.ecid, concat(cif.error_message, ri.error_message) error_message,
                row_number() OVER (PARTITION BY cif.ecid ORDER BY length(concat(cif.error_message, ri.error_message)) desc) as rn
            from composite_instance_fault cif, reference_instance ri
            where cif.ecid = ri.ecid (+) and cif.composite_instance_id = ri.composite_instance_id (+)
          ) where rn = 1) t2,
            __SOAINFRA_SCHEMA__.composite_instance ci, __SOAINFRA_SCHEMA__.composite_instance_fault cif
        where t1.ecid = t2.ecid and
              t1.ecid = cif.ecid and
              t1.cid = ci.id and
              ci.composite_dn not like '%GenerateFault%' and
              ci.composite_dn not like '%CreateTroubleTicketSiebelCommsProvABCSImpl%' and
              ci.composite_dn not like '%CreateOrderFalloutNotification%' and
              cif.created_time >= trunc(sysdate - 2/1440, 'MI') AND cif.created_time < trunc(sysdate - 1/1440, 'MI'))
      )))
group by flow, error_type
order by flow;

