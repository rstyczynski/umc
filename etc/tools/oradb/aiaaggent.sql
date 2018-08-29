-- AIA aggregated entitites count by entity type 
SELECT 
	to_char(sysdate, 'YY-MM-DD HH24:MI')  as "Time",
	entity_type as "EntityType",
	count(*) as "Count"
FROM 
	__AGGENT_SCHEMA__.AIA_AGGREGATED_ENTITIES
GROUP BY 
	entity_type;

