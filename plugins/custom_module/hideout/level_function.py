import pendulum


def process_level(item):
    """
    hideout level 가공
    """
    id = item.get("id")
    level = 0
    construction_time = 0
    update_time = pendulum.now("Asia/Seoul")

    return (
        id, level, construction_time, update_time
    )
