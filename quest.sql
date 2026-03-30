-- 퀘스트 기본 정보
create table if not exists quests (
    id text primary key,
    normalized_name text,
    name_en text,
    name_ko text,
    name_ja text,
    trader_id text,
    experience integer,
    delay_max integer,
    delay_min integer,
    kappa_required boolean,
    min_player_level integer,
    wiki_url text,
    guide_en text,
    guide_ko text,
    guide_ja text,
    sort_order integer,
    update_time timestamptz default now()
);


-- 퀘스트 관계(Relations)
create table if not exists quest_relations (
    quest_id text,
    related_quest_id text,
    relation_type text, -- require(선행), next(후행)
    sort_order integer,
    primary key (quest_id, related_quest_id, relation_type)
);
create index idx_quest_relations_quest_id on quest_relations (quest_id);
create index idx_quest_relations_relation_type on quest_relations (relation_type);

-- 퀘스트 목표(Objectives)
create table if not exists quest_objectives (
    objective_id text primary key,
    quest_id text,
    type text,
    description_en text,
    description_ko text,
    description_ja text,
    count integer,
    found_in_raid boolean,
    sort_order integer,
    raw_data jsonb
);
create index idx_quest_objectives_quest_id on quest_objectives (quest_id);
create index idx_quest_objectives_type on quest_objectives (type);

-- 목표에 필요한 아이템
create table if not exists quest_objective_items (
    objective_id text,
    item_id text,
    item_type text, -- item/questItem/markerItem/requiredKey 등
    sort_order integer,
    primary key (objective_id, item_id, item_type)
);
create index idx_quest_objective_items_objective_id on quest_objective_items (objective_id);
create index idx_quest_objective_items_item_id on quest_objective_items (item_id);

-- 목표에 필요한 키(OR 그룹 지원)
create table if not exists quest_objective_required_keys (
    objective_id text,
    key_group_index integer,
    key_id text,
    primary key (objective_id, key_group_index, key_id)
);
create index idx_quest_objective_required_keys_objective_id on quest_objective_required_keys (objective_id);

-- 목표와 맵의 연관
create table if not exists quest_objective_maps (
    objective_id text,
    map_id text,
    sort_order integer,
    primary key (objective_id, map_id)
);
create index idx_quest_objective_maps_objective_id on quest_objective_maps (objective_id);
create index idx_quest_objective_maps_map_id on quest_objective_maps (map_id);


-- 퀘스트 완료 보상(스킬)
create table if not exists quest_finish_reward_skills (
    quest_id text,
    skill_name text,
    level integer,
    sort_order integer,
    raw_data jsonb,
    primary key (quest_id, skill_name)
);
create index idx_quest_finish_reward_skills_quest_id on quest_finish_reward_skills (quest_id);

-- 퀘스트 완료 보상(트레이더 평판)
create table if not exists quest_finish_reward_trader_standing (
    quest_id text,
    trader_id text,
    standing numeric,
    sort_order integer,
    raw_data jsonb,
    primary key (quest_id, trader_id)
);
create index idx_quest_finish_reward_trader_standing_quest_id on quest_finish_reward_trader_standing (quest_id);

-- 퀘스트 완료 보상(오퍼 해금)
create table if not exists quest_finish_reward_offer_unlock (
    quest_id text,
    offer_id text,
    trader_id text,
    item_id text,
    level integer,
    sort_order integer,
    raw_data jsonb,
    primary key (quest_id, offer_id)
);
create index idx_quest_finish_reward_offer_unlock_quest_id on quest_finish_reward_offer_unlock (quest_id);

-- 퀘스트 완료 보상(아이템)
create table if not exists quest_finish_reward_items (
    quest_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (quest_id, item_id)
);
create index idx_quest_finish_reward_items_quest_id on quest_finish_reward_items (quest_id);
create index idx_quest_finish_reward_items_item_id on quest_finish_reward_items (item_id);

-- 퀘스트 완료 보상(제작 해금)
create table if not exists quest_finish_reward_craft_unlocks (
    quest_id text,
    craft_id text,
    station_level integer,
    sort_order integer,
    primary key (quest_id, craft_id)
);
create index idx_quest_finish_reward_craft_unlocks_quest_id on quest_finish_reward_craft_unlocks (quest_id);
create index idx_quest_finish_reward_craft_unlocks_craft_id on quest_finish_reward_craft_unlocks (craft_id);

-- 퀘스트 완료 보상(아이템)
create table if not exists quest_finish_reward_items (
    quest_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (quest_id, item_id)
);
create index idx_quest_finish_reward_items_quest_id on quest_finish_reward_items (quest_id);
create index idx_quest_finish_reward_items_item_id on quest_finish_reward_items (item_id);
