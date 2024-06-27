import pendulum


def get_today():
    now = pendulum.now()

    # 년, 월, 일 추출
    year = now.year
    month = now.month
    day = now.day

    return f"{year}_{month}_{day}"


def return_script():
    today = get_today()

    return f"pg_dump -h 172.17.0.2 -U tkl tkl > /home/latest_data/{today}_backup.sql"