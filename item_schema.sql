create table if not exists items (
    id text primary key,
    parent_category text,
    category text,
    name_en text,
    name_ko text,
    name_ja text,
    normalized_name text,
    weight numeric,
    width integer,
    height integer,
    image text,
    updated_at timestamptz default now()
);
create index if not exists idx_items_parent_category on items(parent_category);
create index if not exists idx_items_category on items(category);
create index if not exists idx_items_normalized_name on items(normalized_name);
create index if not exists idx_items_updated_at on items(updated_at desc);

create table if not exists item_penalties (
    item_id text primary key,
    ergonomics_penalty numeric,
    turn_speed_penalty numeric,
    movement_speed_penalty numeric,
    distance_modifier numeric
);

create table if not exists weapon_items (
    item_id text primary key,
    caliber text,
    fire_rate integer,
    ergonomics integer,
    recoil_horizontal integer,
    recoil_vertical integer,
    default_ammo_item_id text,
    is_single_fire boolean default false,
    is_full_auto boolean default false,
    is_burst_fire boolean default false,
    is_double_action boolean default false,
    is_double_tap boolean default false,
    is_semi_auto boolean default false
);

create table if not exists weapon_allowed_ammo (
    item_id text,
    ammo_item_id text,
    primary key (item_id, ammo_item_id)
);
create index if not exists idx_weapon_allowed_ammo_ammo_item_id
    on weapon_allowed_ammo(ammo_item_id);

create table if not exists ammo_items (
    item_id text primary key,
    damage integer,
    armor_damage integer,
    penetration_power integer,
    recoil_modifier numeric,
    accuracy_modifier numeric,
    heavy_bleed_modifier numeric,
    light_bleed_modifier numeric
);

create table if not exists ammo_efficiency (
    ammo_item_id text,
    target_name text,
    value_1 integer,
    value_2 integer,
    value_3 integer,
    value_4 integer,
    value_5 integer,
    value_6 integer,
    primary key (ammo_item_id, target_name)
);
create index if not exists idx_ammo_efficiency_target_name
    on ammo_efficiency(target_name);


create table if not exists melee_items (
    item_id text primary key,
    hit_radius numeric,
    slash_damage integer,
    stab_damage integer
);


create table if not exists throwable_items (
    item_id text primary key,
    throwable_type text,
    fuse numeric,
    fragments integer,
    contusion_radius numeric,
    min_explosion_distance numeric,
    max_explosion_distance numeric
);

create table if not exists storage_items (
    item_id text primary key,
    storage_type text,
    capacity integer
);
create index if not exists idx_storage_items_storage_type
    on storage_items(storage_type);

create table if not exists storage_grids (
    item_id text,
    grid_index integer,
    width integer,
    height integer,
    primary key (item_id, grid_index)
);

create table if not exists protection_items (
    item_id text primary key,
    protection_type text,
    armor_class integer,
    durability integer,
    material text,
    ricochet_y numeric,
    deafening text,
    blindness_protection numeric,
    is_head_top boolean default false,
    is_head_nape boolean default false,
    is_head_ears boolean default false,
    is_head_face boolean default false,
    is_head_jaws boolean default false,
    is_head_eyes boolean default false,
    is_thorax_throat boolean default false,
    is_thorax_neck boolean default false,
    is_thorax boolean default false,
    is_upper_back boolean default false,
    is_stomach boolean default false,
    is_left_side boolean default false,
    is_right_side boolean default false,
    is_lower_back boolean default false,
    is_groin boolean default false,
    is_buttocks boolean default false,
    is_left_shoulder boolean default false,
    is_right_shoulder boolean default false,
    is_front_plate boolean default false,
    is_back_plate boolean default false,
    is_left_plate boolean default false,
    is_right_plate boolean default false,
    is_side_plate boolean default false
);
create index if not exists idx_protection_items_protection_type
    on protection_items(protection_type);

create table if not exists consumable_items (
    item_id text primary key,
    consumable_type text,
    energy integer,
    hydration integer,
    units integer,
    use_time numeric,
    hitpoints integer,
    painkiller_duration integer,
    energy_impact integer,
    hydration_impact integer
);
create index if not exists idx_consumable_items_consumable_type
    on consumable_items(consumable_type);

create table if not exists consumable_cures (
    item_id text,
    cure text,
    primary key (item_id, cure)
);
create index if not exists idx_consumable_cures_cure
    on consumable_cures(cure);

create table if not exists consumable_stim_effects (
    item_id text,
    effect_index integer,
    effect_type text,
    value numeric,
    delay integer,
    duration integer,
    skill_name text,
    primary key (item_id, effect_index)
);
create index if not exists idx_consumable_stim_effects_effect_type
    on consumable_stim_effects(effect_type);

create table if not exists usage_items (
    item_id text primary key,
    max_uses integer
);
