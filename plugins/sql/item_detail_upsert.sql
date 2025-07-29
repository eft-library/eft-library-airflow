INSERT INTO item_detail_i18n (
    id,
    hideout_items,
    used_in_crafts,
    rewarded_by_npcs,
    rewarded_by_quests,
    rewarded_by_quests_offer_unlock,
    rewarded_by_quests_craft_unlock,
    required_by_quest_item,
    required_by_quest_item_array
)
WITH target_item AS (
    SELECT *
    FROM item_i18n
    ORDER BY id
    OFFSET %s LIMIT %s
),

-- 🏗️ 은신처 아이템 요구 정보
hideout_agg AS (
    SELECT thir.item_id,
           json_agg(jsonb_build_object(
               'id', thir.id,
               'level_id', thir.level_id,
               'name', thir.name,
               'quantity', thir.quantity,
               'count', thir.count,
               'image', thir.image,
               'item_id', thir.item_id,
               'master_name', thm.name,
               'master_id', thm.id
           )) AS hideout_items
    FROM hideout_item_require_i18n thir
         LEFT JOIN hideout_master_i18n thm
            ON SPLIT_PART(thir.level_id, '-', 1) = thm.id
    WHERE thir.item_id IS NOT NULL
    GROUP BY thir.item_id
),

-- 🏗️ 은신처 제작 정보
crafts_agg AS (
    SELECT elem.required_item_id AS item_id,
           json_agg(jsonb_build_object(
               'id', thc.id,
               'name', thc.name,
               'level_id', thc.level_id,
               'level', thc.level,
               'duration', thc.duration,
               'req_item', thc.req_item,
               'reward_item_id', thc.reward_item_id,
               'image', thc.image,
               'quantity', thc.quantity,
               'master_name', thm.name,
               'master_id', thm.id
           )) AS used_in_crafts
    FROM hideout_crafts_i18n thc
         LEFT JOIN LATERAL jsonb_array_elements(thc.req_item) elem_raw ON TRUE
         LEFT JOIN LATERAL (SELECT elem_raw -> 'item' ->> 'id' AS required_item_id) elem ON TRUE
         LEFT JOIN hideout_master_i18n thm
            ON SPLIT_PART(thc.level_id, '-', 1) = thm.id
    WHERE elem.required_item_id IS NOT NULL
    GROUP BY elem.required_item_id
),

-- 🛒 NPC 바터 정보
barter_agg AS (
    SELECT reward.reward_item_id AS item_id,
           json_agg(jsonb_build_object(
               'npc_id', n.id,
               'npc_image', n.image,
               'npc_name', n.name,
               'barter_info', jsonb_build_object(
                   'level', barter ->> 'level',
                   'rewardItems', reward_raw,
                   'requiredItems', barter -> 'requiredItems'
               )
           )) AS rewarded_by_npcs
    FROM npc_i18n n
         LEFT JOIN LATERAL jsonb_array_elements(n.barter_info) AS barter ON TRUE
         LEFT JOIN LATERAL jsonb_array_elements(barter -> 'rewardItems') AS reward_raw ON TRUE
         LEFT JOIN LATERAL (SELECT reward_raw -> 'item' ->> 'id' AS reward_item_id) reward ON TRUE
    WHERE reward.reward_item_id IS NOT NULL
    GROUP BY reward.reward_item_id
),

-- 🎯 퀘스트 보상 정보
quests_reward_agg AS (
    SELECT r.reward_item_id AS item_id,
           json_agg(jsonb_build_object(
               'quest_id', qa.id,
               'name', qa.name,
               'npc_name', tn.name,
               'npc_image', tn.image,
               'url_mapping', qa.url_mapping,
               'reward', reward_elem
           )) AS rewarded_by_quests
    FROM quest_i18n qa
         LEFT JOIN npc_i18n tn ON qa.npc_id = tn.id
         LEFT JOIN LATERAL jsonb_array_elements(qa.finish_rewards -> 'items') AS reward_elem ON TRUE
         LEFT JOIN LATERAL (SELECT reward_elem -> 'item' ->> 'id' AS reward_item_id) r ON TRUE
    WHERE r.reward_item_id IS NOT NULL
    GROUP BY r.reward_item_id
),

-- 🎯 offerUnlock
quests_offer_unlock_agg AS (
    SELECT r.reward_item_id AS item_id,
           json_agg(jsonb_build_object(
               'quest_id', qa.id,
               'name', qa.name,
               'npc_name', tn.name,
               'npc_image', tn.image,
               'url_mapping', qa.url_mapping,
               'reward', reward_elem
           )) AS rewarded_by_quests_offer_unlock
    FROM quest_i18n qa
         LEFT JOIN npc_i18n tn ON qa.npc_id = tn.id
         LEFT JOIN LATERAL jsonb_array_elements(qa.finish_rewards -> 'offerUnlock') AS reward_elem ON TRUE
         LEFT JOIN LATERAL (SELECT reward_elem -> 'item' ->> 'id' AS reward_item_id) r ON TRUE
    WHERE r.reward_item_id IS NOT NULL
    GROUP BY r.reward_item_id
),

-- 🎯 craftUnlock
quests_craft_unlock_agg AS (
    SELECT r.reward_item_id AS item_id,
           json_agg(jsonb_build_object(
               'quest_id', qa.id,
               'name', qa.name,
               'npc_name', tn.name,
               'npc_image', tn.image,
               'url_mapping', qa.url_mapping,
               'reward', reward_item
           )) AS rewarded_by_quests_craft_unlock
    FROM quest_i18n qa
         LEFT JOIN npc_i18n tn ON qa.npc_id = tn.id
         LEFT JOIN LATERAL jsonb_array_elements(qa.finish_rewards -> 'craftUnlock') AS craft_unlock ON TRUE
         LEFT JOIN LATERAL jsonb_array_elements(craft_unlock -> 'rewardItems') AS reward_item ON TRUE
         LEFT JOIN LATERAL (SELECT reward_item -> 'item' ->> 'id' AS reward_item_id) r ON TRUE
    WHERE r.reward_item_id IS NOT NULL
    GROUP BY r.reward_item_id
),

-- ❗ questItem
required_quest_item_agg AS (
    SELECT id_map.item_id,
           json_agg(jsonb_build_object(
               'quest_id', q.id,
               'name', q.name,
               'npc_name', tn.name,
               'npc_image', tn.image,
               'url_mapping', q.url_mapping,
               'objective', objective
           )) AS required_by_quest_item
    FROM quest_i18n q
         LEFT JOIN npc_i18n tn ON q.npc_id = tn.id
         LEFT JOIN LATERAL jsonb_array_elements(q.objectives) AS objective ON TRUE
         LEFT JOIN LATERAL (SELECT objective -> 'questItem' ->> 'id' AS item_id) id_map ON TRUE
    WHERE id_map.item_id IS NOT NULL
      AND objective ->> 'type' IN ('findQuestItem', 'giveQuestItem')
    GROUP BY id_map.item_id
),

-- ❗ items 배열 기반 quest
required_quest_items_array_agg AS (
    SELECT id_map.item_id,
           json_agg(jsonb_build_object(
               'quest_id', q.id,
               'name', q.name,
               'npc_name', tn.name,
               'npc_image', tn.image,
               'url_mapping', q.url_mapping,
               'objective', obj
           )) AS required_by_quest_item_array
    FROM quest_i18n q
         LEFT JOIN npc_i18n tn ON q.npc_id = tn.id
         LEFT JOIN LATERAL jsonb_array_elements(q.objectives) AS obj ON TRUE
         LEFT JOIN LATERAL jsonb_array_elements(obj -> 'items') AS item ON TRUE
         LEFT JOIN LATERAL (SELECT item ->> 'id' AS item_id) id_map ON TRUE
    WHERE id_map.item_id IS NOT NULL
      AND obj ->> 'type' IN ('plantItem', 'giveItem', 'findItem')
    GROUP BY id_map.item_id
)

SELECT ti.id,
       COALESCE(h.hideout_items, '[]') AS hideout_items,
       COALESCE(c.used_in_crafts, '[]') AS used_in_crafts,
       COALESCE(b.rewarded_by_npcs, '[]') AS rewarded_by_npcs,
       COALESCE(qr.rewarded_by_quests, '[]') AS rewarded_by_quests,
       COALESCE(qo.rewarded_by_quests_offer_unlock, '[]') AS rewarded_by_quests_offer_unlock,
       COALESCE(qc.rewarded_by_quests_craft_unlock, '[]') AS rewarded_by_quests_craft_unlock,
       COALESCE(rqi.required_by_quest_item, '[]') AS required_by_quest_item,
       COALESCE(rqia.required_by_quest_item_array, '[]') AS required_by_quest_item_array
FROM target_item ti
     LEFT JOIN hideout_agg h ON ti.id = h.item_id
     LEFT JOIN crafts_agg c ON ti.id = c.item_id
     LEFT JOIN barter_agg b ON ti.id = b.item_id
     LEFT JOIN quests_reward_agg qr ON ti.id = qr.item_id
     LEFT JOIN quests_offer_unlock_agg qo ON ti.id = qo.item_id
     LEFT JOIN quests_craft_unlock_agg qc ON ti.id = qc.item_id
     LEFT JOIN required_quest_item_agg rqi ON ti.id = rqi.item_id
     LEFT JOIN required_quest_items_array_agg rqia ON ti.id = rqia.item_id
ON CONFLICT (id) DO UPDATE
    SET hideout_items                   = EXCLUDED.hideout_items,
        used_in_crafts                  = EXCLUDED.used_in_crafts,
        rewarded_by_npcs                = EXCLUDED.rewarded_by_npcs,
        rewarded_by_quests              = EXCLUDED.rewarded_by_quests,
        rewarded_by_quests_offer_unlock = EXCLUDED.rewarded_by_quests_offer_unlock,
        rewarded_by_quests_craft_unlock = EXCLUDED.rewarded_by_quests_craft_unlock,
        required_by_quest_item          = EXCLUDED.required_by_quest_item,
        required_by_quest_item_array    = EXCLUDED.required_by_quest_item_array,
        update_time                     = NOW();
