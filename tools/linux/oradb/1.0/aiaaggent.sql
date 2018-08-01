-- AIA aggregated entitites count by entity type 
SELECT 
	to_char(sysdate, 'YY-MM-DD HH24:MI')  as "time",
	entity_type as "entity_type",
	count(*) as "count"
FROM 
	__AGGENT_SCHEMA__.AIA_AGGREGATED_ENTITIES
GROUP BY 
	entity_type;

