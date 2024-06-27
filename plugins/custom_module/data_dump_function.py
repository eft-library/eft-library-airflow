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

    return f"""
        source ~/.bashrc
        echo "Executing PostgreSQL Command - pg_dump"
        pg_dump -h $DB -U tkl tkl > /home/latest_data/{today}_backup.sql
        echo $?
        """