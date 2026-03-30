(
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

create table if not exists quest_objectives
(
    objective_id text,
    quest_id text,
    objective_type text,
    description_en text,
    description_ko text,
    description_ja text,
    location_in_map boolean,
    raw_data jsonb,
    sort_order integer,
    primary key (objective_id, quest_id)
);
create index idx_quest_objectives_quest_id on quest_objectives (quest_id);
create index idx_quest_objectives_quest_id_sort_order on quest_objectives (quest_id, sort_order);
create index idx_quest_objectives_objective_type on quest_objectives (objective_type);

create table if not exists quest_objective_items
(
    objective_id text,
    item_type text, -- all item / questItem / markerItem / requiredKey
    item_id text,
    sort_order integer,
    primary key (objective_id, item_type, item_id)
);
create index idx_quest_objective_items_item_id on quest_objective_items (item_id);
create index idx_quest_objective_items_item_type on quest_objective_items (item_type);
create index idx_quest_objective_items_objective_id_item_type on quest_objective_items (objective_id, item_type);

create table if not exists quest_objective_maps
(
    objective_id text,
    map_id text,
    sort_order integer,
    primary key (objective_id, map_id)
);
create index idx_quest_objective_maps_map_id on quest_objective_maps (map_id);

create table if not exists quest_relations
(
    quest_id text,
    related_quest_id text,
    relation_type text, -- require / next
    sort_order integer,
    primary key (quest_id, related_quest_id, relation_type)
);
create index idx_quest_relations_related_quest_id on quest_relations (related_quest_id);
create index idx_quest_relations_relation_type on quest_relations (relation_type);

create table if not exists quest_finish_rewards
(
    quest_id text,
    reward_type text, -- skill_level / offer_unlock / trader_standing
    target_id text,   -- trader_id, skill_name 등
    reward_value numeric,
    raw_data jsonb,
    sort_order integer,
    primary key (quest_id, reward_type, target_id)
);
create index idx_quest_finish_rewards_quest_id on quest_finish_rewards (quest_id);
create index idx_quest_finish_rewards_reward_type on quest_finish_rewards (reward_type);
create index idx_quest_finish_rewards_target_id on quest_finish_rewards (target_id);

create table if not exists quest_finish_reward_items
(
    quest_id text,
    item_id text,
    quantity integer,
    sort_order integer,
    primary key (quest_id, item_id)
);
create index idx_quest_finish_reward_items_item_id on quest_finish_reward_items (item_id);

create table if not exists quest_finish_reward_craft_unlocks
(
    quest_id text,
    craft_id text,
    station_level integer,
    sort_order integer,
    primary key (quest_id, craft_id)
);
create index idx_quest_finish_reward_craft_unlocks_craft_id on quest_finish_reward_craft_unlocks (craft_id);

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

-- 선행 퀘스트(Requirements)
create table if not exists quest_requirements (
    quest_id text,
    required_quest_id text,
    sort_order integer,
    primary key (quest_id, required_quest_id)
);
create index idx_quest_requirements_quest_id on quest_requirements (quest_id);

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

-- 퀘스트 완료 보상(일반)
create table if not exists quest_finish_rewards (
    quest_id text,
    reward_type text, -- skill_level/offer_unlock/trader_standing 등
    target_id text,   -- trader_id, skill_name 등
    reward_value numeric,
    sort_order integer,
    raw_data jsonb,
    primary key (quest_id, reward_type, target_id)
);
create index idx_quest_finish_rewards_quest_id on quest_finish_rewards (quest_id);
create index idx_quest_finish_rewards_reward_type on quest_finish_rewards (reward_type);
create index idx_quest_finish_rewards_target_id on quest_finish_rewards (target_id);

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