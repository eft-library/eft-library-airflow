INSERT INTO tkl_new_quest (
    id,
    name,
    npc_name,
    task_requirements,
    objectives,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    npc_name = EXCLUDED.npc_name,
    task_requirements = EXCLUDED.task_requirements,
    objectives = EXCLUDED.objectives,
    update_time = EXCLUDED.update_time
