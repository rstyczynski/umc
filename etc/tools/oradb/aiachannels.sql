-- AIA order main channels 
select created_time as "Time", channel as "Channel", count(1) as "Count" from (
select to_char(created_time, 'YY-MM-DD HH24:MI') created_time, title,
case
  when SUBSTR(title, 1,3)='SBL' then 'SBL'
  when SUBSTR(title, 1,3)='IVR' then 'IVR'
  when SUBSTR(title, 1,3)='WEB' then 'WEB'
  when SUBSTR(title, 1,3)='PNT' then 'PNT'
  when SUBSTR(title, 1,3)='TIL' then 'TIL'
  else '-OTHER'
end channel
from __SOAINFRA_SCHEMA__.composite_instance
where   composite_dn like 'default/ProcessSalesOrderFulfillmentSiebelCommsJMSConsumer%' and
        created_time >= trunc(sysdate - 2/1440, 'MI') AND created_time < trunc(sysdate - 1/1440, 'MI'))	
group by created_time, channel

