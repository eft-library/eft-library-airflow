INSERT INTO quest_i18n (
    id,
    name,
    npc_id,
    lightkeeper_required,
    kappa_required,
    task_requirements,
    objectives,
    wiki_url,
    finish_rewards,
    url_mapping,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    npc_id = EXCLUDED.npc_id,
    lightkeeper_required = EXCLUDED.lightkeeper_required,
    kappa_required = EXCLUDED.kappa_required,
    task_requirements = EXCLUDED.task_requirements,
    objectives = EXCLUDED.objectives,
    wiki_url = EXCLUDED.wiki_url,
    url_mapping = EXCLUDED.url_mapping,
    finish_rewards = EXCLUDED.finish_rewards,
    update_time = EXCLUDED.update_time
