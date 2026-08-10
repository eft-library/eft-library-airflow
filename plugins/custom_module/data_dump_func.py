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
    "where_am_i",
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
    "kord_breach_modifier",
    "kord_breach_modifier_conflict",
    "user_kord_breach_preset",
    "user_kord_breach_preset_modifier",
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
