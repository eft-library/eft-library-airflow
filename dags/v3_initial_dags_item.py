import json
import pendulum
import os

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values
from airflow.task.trigger_rule import TriggerRule

from custom_module.graphql_func import get_graphql
from custom_module.v3.item_task_func import (
    generate_item_graphql,
    v3_item_row_process,
    assign_unique_normalized_names,
    v3_item_penalties_row,
    v3_weapon_items_row,
    v3_weapon_allowed_ammo_rows,
    v3_ammo_items_row,
    v3_melee_items_row,
    v3_throwable_items_row,
    v3_storage_items_and_grids,
    v3_protection_items_row,
    v3_consumable_items_and_effects,
    v3_usage_items_row,
    get_efficiency,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_initial_item_en_list.json"
ko_path = "/opt/airflow/tmp/v3_initial_item_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_initial_item_ja_list.json"

with DAG(
    dag_id="v3_initial_dags_item",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule=None,
    tags=["postgresql", "tarkov-dev-api", "initial-load", "manual-only"],
    catchup=False,
) as dag:

    def fetch_item():
        item_list_en = get_graphql(generate_item_graphql("en"))
        item_list_ko = get_graphql(generate_item_graphql("ko"))
        item_list_ja = get_graphql(generate_item_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["items"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["items"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["items"], f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def upsert_item(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = set(item_en_dict) & set(item_ko_dict) & set(item_ja_dict)

        # ammo_efficiency
        ammo_efficiency_rows = []
        for iid in item_ids:
            item = item_en_dict[iid]
            props = item.get("properties")
            if not isinstance(props, dict):
                continue
            # ammo_items에 들어가는 아이템만 처리
            if not ("damage" in props or "penetrationPower" in props):
                continue
            eff = get_efficiency(item.get("name"))
            if eff and len(eff) == 6:
                ammo_efficiency_rows.append((iid, *eff))
        # items
        item_rows = [
            v3_item_row_process(item_en_dict[iid], item_ko_dict[iid], item_ja_dict[iid])
            for iid in item_ids
        ]

        # item_penalties
        def has_any_penalty(row):
            return any(x is not None for x in row[1:])

        penalties_rows = [
            r
            for iid in item_ids
            if has_any_penalty(r := v3_item_penalties_row(item_en_dict[iid]))
        ]

        # weapon_items
        weapon_rows = [
            v3_weapon_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_weapon_items_row(item_en_dict[iid])
        ]

        # weapon_allowed_ammo
        allowed_ammo_rows = []
        for iid in item_ids:
            allowed_ammo_rows.extend(v3_weapon_allowed_ammo_rows(item_en_dict[iid]))

        # ammo_items
        ammo_rows = [
            v3_ammo_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_ammo_items_row(item_en_dict[iid])
        ]

        # melee_items
        melee_rows = [
            v3_melee_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_melee_items_row(item_en_dict[iid])
        ]

        # throwable_items
        throwable_rows = [
            v3_throwable_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_throwable_items_row(item_en_dict[iid])
        ]

        # storage_items, storage_grids
        storage_rows, grid_rows = [], []
        for iid in item_ids:
            srow, grows = (
                v3_storage_items_and_grids(item_en_dict[iid])
                if v3_storage_items_and_grids(item_en_dict[iid])
                else (None, [])
            )
            if srow:
                storage_rows.append(srow)
            grid_rows.extend(grows)

        # protection_items
        protection_rows = [
            v3_protection_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_protection_items_row(item_en_dict[iid])
        ]

        # consumable_items, consumable_cures, consumable_stim_effects
        consumable_rows, cure_rows, stim_rows = [], [], []
        for iid in item_ids:
            irow, crows, srows = v3_consumable_items_and_effects(item_en_dict[iid])
            if irow:
                consumable_rows.append(irow)
            cure_rows.extend(crows)
            stim_rows.extend(srows)

        # usage_items
        usage_rows = [
            v3_usage_items_row(item_en_dict[iid])
            for iid in item_ids
            if v3_usage_items_row(item_en_dict[iid])
        ]

        hook = PostgresHook(postgres_conn_id)
        with closing(hook.get_conn()) as conn, conn.cursor() as cur:
            cur.execute("select id, normalized_name from items where normalized_name is not null")
            existing_normalized_names_by_id = dict(cur.fetchall())
            item_rows = assign_unique_normalized_names(
                item_rows, existing_normalized_names_by_id
            )

            # 하위 테이블 전체 비우기 (items 제외)
            cur.execute("""
                truncate table
                    item_penalties,
                    weapon_items,
                    weapon_allowed_ammo,
                    ammo_items,
                    melee_items,
                    throwable_items,
                    storage_items,
                    storage_grids,
                    protection_items,
                    consumable_items,
                    consumable_cures,
                    consumable_stim_effects,
                    usage_items,
                    ammo_efficiency
                restart identity cascade;
            """)
            # items
            execute_values(
                cur,
                """
                insert into items (
                    id, parent_category, category, name_en, name_ko, name_ja, normalized_name, weight, width, height, image
                ) values %s
                on conflict (id) do update set
                    parent_category=excluded.parent_category,
                    category=excluded.category,
                    name_en=excluded.name_en,
                    name_ko=excluded.name_ko,
                    name_ja=excluded.name_ja,
                    normalized_name=excluded.normalized_name,
                    weight=excluded.weight,
                    width=excluded.width,
                    height=excluded.height,
                    image=excluded.image,
                    update_time=now()
                """,
                item_rows,
            )

            # ammo_efficiency
            if ammo_efficiency_rows:
                execute_values(
                    cur,
                    """
                    insert into ammo_efficiency (
                        ammo_item_id, value_1, value_2, value_3, value_4, value_5, value_6
                    ) values %s
                    on conflict (ammo_item_id) do update set
                        value_1=excluded.value_1,
                        value_2=excluded.value_2,
                        value_3=excluded.value_3,
                        value_4=excluded.value_4,
                        value_5=excluded.value_5,
                        value_6=excluded.value_6
                    """,
                    ammo_efficiency_rows,
                )

            # item_penalties
            if penalties_rows:
                execute_values(
                    cur,
                    """
                    insert into item_penalties (
                        item_id, ergonomics_penalty, turn_speed_penalty, movement_speed_penalty, distance_modifier
                    ) values %s
                    on conflict (item_id) do update set
                        ergonomics_penalty=excluded.ergonomics_penalty,
                        turn_speed_penalty=excluded.turn_speed_penalty,
                        movement_speed_penalty=excluded.movement_speed_penalty,
                        distance_modifier=excluded.distance_modifier
                """,
                    penalties_rows,
                )

            # weapon_items
            if weapon_rows:
                execute_values(
                    cur,
                    """
                    insert into weapon_items (
                        item_id, caliber, fire_rate, ergonomics, recoil_horizontal, recoil_vertical, default_ammo_item_id,
                        is_single_fire, is_full_auto, is_burst_fire, is_double_action, is_double_tap, is_semi_auto
                    ) values %s
                    on conflict (item_id) do update set
                        caliber=excluded.caliber,
                        fire_rate=excluded.fire_rate,
                        ergonomics=excluded.ergonomics,
                        recoil_horizontal=excluded.recoil_horizontal,
                        recoil_vertical=excluded.recoil_vertical,
                        default_ammo_item_id=excluded.default_ammo_item_id,
                        is_single_fire=excluded.is_single_fire,
                        is_full_auto=excluded.is_full_auto,
                        is_burst_fire=excluded.is_burst_fire,
                        is_double_action=excluded.is_double_action,
                        is_double_tap=excluded.is_double_tap,
                        is_semi_auto=excluded.is_semi_auto
                """,
                    weapon_rows,
                )

            # weapon_allowed_ammo
            if allowed_ammo_rows:
                execute_values(
                    cur,
                    """
                    insert into weapon_allowed_ammo (
                        item_id, ammo_item_id
                    ) values %s
                    on conflict (item_id, ammo_item_id) do nothing
                """,
                    allowed_ammo_rows,
                )

            # ammo_items
            if ammo_rows:
                execute_values(
                    cur,
                    """
                    insert into ammo_items (
                        item_id, damage, armor_damage, penetration_power, recoil_modifier, accuracy_modifier, heavy_bleed_modifier, light_bleed_modifier
                    ) values %s
                    on conflict (item_id) do update set
                        damage=excluded.damage,
                        armor_damage=excluded.armor_damage,
                        penetration_power=excluded.penetration_power,
                        recoil_modifier=excluded.recoil_modifier,
                        accuracy_modifier=excluded.accuracy_modifier,
                        heavy_bleed_modifier=excluded.heavy_bleed_modifier,
                        light_bleed_modifier=excluded.light_bleed_modifier
                """,
                    ammo_rows,
                )

            # melee_items
            if melee_rows:
                execute_values(
                    cur,
                    """
                    insert into melee_items (
                        item_id, hit_radius, slash_damage, stab_damage
                    ) values %s
                    on conflict (item_id) do update set
                        hit_radius=excluded.hit_radius,
                        slash_damage=excluded.slash_damage,
                        stab_damage=excluded.stab_damage
                """,
                    melee_rows,
                )

            # throwable_items
            if throwable_rows:
                execute_values(
                    cur,
                    """
                    insert into throwable_items (
                        item_id, throwable_type, fuse, fragments, contusion_radius, min_explosion_distance, max_explosion_distance
                    ) values %s
                    on conflict (item_id) do update set
                        throwable_type=excluded.throwable_type,
                        fuse=excluded.fuse,
                        fragments=excluded.fragments,
                        contusion_radius=excluded.contusion_radius,
                        min_explosion_distance=excluded.min_explosion_distance,
                        max_explosion_distance=excluded.max_explosion_distance
                """,
                    throwable_rows,
                )

            # storage_items
            if storage_rows:
                execute_values(
                    cur,
                    """
                    insert into storage_items (
                        item_id, storage_type, capacity
                    ) values %s
                    on conflict (item_id) do update set
                        storage_type=excluded.storage_type,
                        capacity=excluded.capacity
                """,
                    storage_rows,
                )

            # storage_grids
            if grid_rows:
                execute_values(
                    cur,
                    """
                    insert into storage_grids (
                        item_id, grid_index, width, height
                    ) values %s
                    on conflict (item_id, grid_index) do update set
                        width=excluded.width,
                        height=excluded.height
                """,
                    grid_rows,
                )

            # protection_items
            if protection_rows:
                execute_values(
                    cur,
                    """
                    insert into protection_items (
                        item_id, protection_type, armor_class, durability, material, ricochet_y, deafening, blindness_protection,
                        is_head_top, is_head_nape, is_head_ears, is_head_face, is_head_jaws, is_head_eyes, is_thorax_throat, is_thorax_neck, is_thorax, is_upper_back, is_stomach, is_left_side, is_right_side, is_lower_back, is_groin, is_buttocks, is_left_shoulder, is_right_shoulder, is_front_plate, is_back_plate, is_left_plate, is_right_plate, is_side_plate
                    ) values %s
                    on conflict (item_id) do update set
                        protection_type=excluded.protection_type,
                        armor_class=excluded.armor_class,
                        durability=excluded.durability,
                        material=excluded.material,
                        ricochet_y=excluded.ricochet_y,
                        deafening=excluded.deafening,
                        blindness_protection=excluded.blindness_protection,
                        is_head_top=excluded.is_head_top,
                        is_head_nape=excluded.is_head_nape,
                        is_head_ears=excluded.is_head_ears,
                        is_head_face=excluded.is_head_face,
                        is_head_jaws=excluded.is_head_jaws,
                        is_head_eyes=excluded.is_head_eyes,
                        is_thorax_throat=excluded.is_thorax_throat,
                        is_thorax_neck=excluded.is_thorax_neck,
                        is_thorax=excluded.is_thorax,
                        is_upper_back=excluded.is_upper_back,
                        is_stomach=excluded.is_stomach,
                        is_left_side=excluded.is_left_side,
                        is_right_side=excluded.is_right_side,
                        is_lower_back=excluded.is_lower_back,
                        is_groin=excluded.is_groin,
                        is_buttocks=excluded.is_buttocks,
                        is_left_shoulder=excluded.is_left_shoulder,
                        is_right_shoulder=excluded.is_right_shoulder,
                        is_front_plate=excluded.is_front_plate,
                        is_back_plate=excluded.is_back_plate,
                        is_left_plate=excluded.is_left_plate,
                        is_right_plate=excluded.is_right_plate,
                        is_side_plate=excluded.is_side_plate
                """,
                    protection_rows,
                )

            # consumable_items
            if consumable_rows:
                execute_values(
                    cur,
                    """
                    insert into consumable_items (
                        item_id, consumable_type, energy, hydration, units, use_time, hitpoints, painkiller_duration, energy_impact, hydration_impact
                    ) values %s
                    on conflict (item_id) do update set
                        consumable_type=excluded.consumable_type,
                        energy=excluded.energy,
                        hydration=excluded.hydration,
                        units=excluded.units,
                        use_time=excluded.use_time,
                        hitpoints=excluded.hitpoints,
                        painkiller_duration=excluded.painkiller_duration,
                        energy_impact=excluded.energy_impact,
                        hydration_impact=excluded.hydration_impact
                """,
                    consumable_rows,
                )

            # consumable_cures
            if cure_rows:
                execute_values(
                    cur,
                    """
                    insert into consumable_cures (
                        item_id, cure
                    ) values %s
                    on conflict (item_id, cure) do nothing
                """,
                    cure_rows,
                )

            # consumable_stim_effects
            if stim_rows:
                execute_values(
                    cur,
                    """
                    insert into consumable_stim_effects (
                        item_id, effect_index, effect_type, value, delay, duration, skill_name
                    ) values %s
                    on conflict (item_id, effect_index) do update set
                        effect_type=excluded.effect_type,
                        value=excluded.value,
                        delay=excluded.delay,
                        duration=excluded.duration,
                        skill_name=excluded.skill_name
                """,
                    stim_rows,
                )

            # usage_items
            if usage_rows:
                execute_values(
                    cur,
                    """
                    insert into usage_items (
                        item_id, max_uses
                    ) values %s
                    on conflict (item_id) do update set
                        max_uses=excluded.max_uses
                """,
                    usage_rows,
                )

            conn.commit()

    def remove_json_files():
        files = [en_path, ko_path, ja_path]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_item_task = PythonOperator(
        task_id="fetch_item",
        python_callable=fetch_item,
    )

    upsert_item_task = PythonOperator(
        task_id="upsert_item",
        python_callable=upsert_item,
        op_args=["platform_db"],
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    fetch_item_task >> upsert_item_task >> remove_json_files_task
