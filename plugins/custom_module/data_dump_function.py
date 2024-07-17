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
        pg_dump -h $DB -U tkl --inserts tkl > /home/latest_data/{today}_backup.sql
        echo $?
        """

def remove_old_file_script():
    """
    7일 지난 백업 파일들 제거 하기
    """

    return "find /home/latest_data -type f -mtime +3 -delete"