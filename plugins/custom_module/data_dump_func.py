import pendulum


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

    return f"""
        pg_dump -h 192.168.219.102 -p 13245 -U tkl \
        --inserts \
        prd \
        -t public.boss_i18n \
        -t public.extraction_18n \
        -t public.transit_i18n \
        -t public.main_i18n \
        -t public.menu_group_i18n \
        -t public.community_comments \
        -t public.community_posts \
        -t public.community_posts_reactions \
        -t public.community_posts_views \
        -t public.dynamic_info_i18n \
        -t public.extraction_i18n \
        -t public.information_i18n \
        -t public.main_i18n \
        -t public.map_group_i18n \
        -t public.menu_group_i18n \
        -t public.menu_sub_group_i18n \
        -t public.npc_i18n \
        -t public.progress_item_i18n \
        -t public.quest_i18n \
        -t public.roadmap_node \
        -t public.roadmap_edge \
        -t public.sitemap \
        -t public.story_i18n \
        -t public.story_roadmap_i18n \
        -t public.user_follows \
        -t public.user_hideout \
        -t public.user_info \
        -t public.user_progress_item \
        -t public.user_quest \
        -t public.user_roadmap \
        -t public.where_am_i_i18n \
        -t public.wipe_i18n \
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
