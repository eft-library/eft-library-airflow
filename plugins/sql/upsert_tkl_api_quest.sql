INSERT INTO tkl_api_quest (
    id,
    name_en,
    npc_id,
    lightkeeper_required,
    kappa_required,
    task_requirements,
    objectives,
    finish_rewards,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    npc_id = EXCLUDED.npc_id,
    lightkeeper_required = EXCLUDED.lightkeeper_required,
    kappa_required = EXCLUDED.kappa_required,
    task_requirements = EXCLUDED.task_requirements,
    objectives = EXCLUDED.objectives,
    finish_rewards = EXCLUDED.finish_rewards,
    update_time = EXCLUDED.update_time
