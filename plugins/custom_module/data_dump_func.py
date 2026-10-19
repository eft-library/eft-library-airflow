import pendulum


DATA_DUMP_TABLES = [
    "bosses",
    "maps",
    "map_points",
    "main_contents",
    "menu_groups",
    "menu_sub_groups",
    "news_items",
    "user_info",
    "information",
    "user_roadmap",
    "roadmap_node",
    "roadmap_edge",
    "wipe",
    "user_hideout",
    "sitemap",
    "user_progress_item",
    "progress_item",
    "story",
    "story_roadmap",
    "story_objectives",
    "story_requirements",
    "story_requirement_items",
    "story_objective_items",
    "story_objective_reward_items",
    "story_objective_reward_texts",
    "story_reward_trader_standing",
    "story_reward_items",
    "community_posts",
    "community_posts_views",
    "community_posts_reactions",
    "community_posts_hot_issue",
    "user_follows",
    "community_posts_bookmark",
    "community_comments",
    "community_comments_reactions",
    "user_block",
    "user_penalty",
    "comment_report",
    "post_report",
    "user_report",
    "user_notifications",
    "live_map_floors",
    "live_map_floor_zones",
    "live_map_points",
    "live_map_point_details",
    "live_map_static_points",
    "live_map_story_points",
    "live_map_story_point_details",
    "live_map_story_requirement_points",
    "live_map_story_requirement_point_details",
    "live_map_event_objectives",
    "live_map_events",
    "live_map_event_objective_items",
    "live_map_event_reward_trader_standing",
    "live_map_event_reward_items",
    "live_map_event_reward_texts",
    "live_map_event_point_details",
    "live_map_event_points",
    "quests",
    "quest_objectives",
    "prestige_levels",
    "prestige_conditions",
    "prestige_condition_items",
    "prestige_condition_statuses",
    "prestige_condition_maps",
    "prestige_reward_items",
    "prestige_reward_skills",
    "customizations",
    "customization_items",
    "prestige_reward_customizations",
    "quest_reward_customizations",
    "prestige_transfer_settings",
    "prestige_transfer_filter_values",
    "kord_breach_modifier",
    "kord_breach_modifier_conflict",
    "user_kord_breach_preset",
    "user_kord_breach_preset_modifier",
    # 누락된 게임 기준 데이터 및 현재 가격 (가격 이력은 제외)
    "boss_spawn",
    "boss_item",
    "quest_relations",
    "quest_objective_items",
    "quest_objective_required_keys",
    "quest_objective_maps",
    "quest_finish_reward_skills",
    "quest_finish_reward_trader_standing",
    "quest_finish_reward_offer_unlock",
    "quest_finish_reward_items",
    "quest_finish_reward_craft_unlocks",
    "traders",
    "trader_barters",
    "barter_required_items",
    "barter_reward_items",
    "autocomplete_items",
    "hideout_master",
    "hideout_levels",
    "hideout_item_require",
    "hideout_trader_require",
    "hideout_station_require",
    "hideout_crafts",
    "hideout_craft_require_items",
    "hideout_skill_require",
    "hideout_bonus",
    "items",
    "item_penalties",
    "weapon_items",
    "weapon_allowed_ammo",
    "ammo_items",
    "ammo_efficiency",
    "melee_items",
    "throwable_items",
    "storage_items",
    "storage_grids",
    "protection_items",
    "consumable_items",
    "consumable_cures",
    "consumable_stim_effects",
    "usage_items",
    "price_seasons",
    "item_prices",
    "item_trader_prices",
    # 운영 설정 및 데스크톱 배포 메타데이터 (요청/분석 로그는 제외)
    "deployment_notice",
    "where_am_i_releases",
    "where_am_i_map_aliases",
    # BTR 경로 및 배틀패스 기준 데이터
    "live_map_btr_routes",
    "live_map_btr_route_points",
    "live_map_btr_route_stops",
    "battle_pass_seasons",
    "battle_pass_pages",
    "battle_pass_documents",
    "battle_pass_rewards",
    "battle_pass_reward_requirements",
    # 파티 저장 상태 및 사용자 채팅 설정 (메시지/접속/초대 이력은 제외)
    "live_map_party_rooms",
    "live_map_party_members",
    "live_map_party_markers",
    "live_map_chat_users",
    "live_map_chat_blocks",
    "live_map_chat_restrictions",
    "live_map_chat_invite_preferences",
]


def get_today():
    """
    년, 월, 일 추출
    """
    now = pendulum.now()

    year = now.year
    month = now.month
    day = now.day

    return f"{year}_{month}_{day}"


def dump_script():
    """
    postgresql dump 뜨고 결과 넘기기
    """
    today = get_today()
    table_args = " \\\n        ".join(
        f"-t public.{table_name}" for table_name in DATA_DUMP_TABLES
    )

    return f"""
        pg_dump -h 172.30.1.100 -p 13245 -U tkl \\
        --inserts \\
        {table_args} \\
        platform_db \\
        > /opt/airflow/latest_data/{today}_backup.sql 2>&1

        exit_code=$?
        echo $exit_code
        exit $exit_code
    """


def remove_old_file_script():
    """
    3일 지난 백업 파일들 제거 하기
    """

    return "find /opt/airflow/latest_data -type f -mtime +2 -delete"


def compress_backup_script(file_path: str):
    """
    백업된 .sql 파일을 gzip으로 압축
    """
    return f"gzip -f {file_path}"
