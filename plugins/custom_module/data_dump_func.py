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
        source ~/.bashrc
        echo "Executing PostgreSQL Command - pg_dump"
        pg_dump -h 192.168.219.102 -p 13245 -U tkl --inserts --exclude-table-data=public.item_detail_i18n --exclude-table-data=public.item_price_i18n --exclude-table-data=public.user_footprint --exclude-table=public.item_i18n --exclude-table=public.search_i18n --exclude-table=public.item_price_history_i18n prd > /opt/airflow/latest_data/{today}_backup.sql
        echo $?
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
