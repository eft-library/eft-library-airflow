import pendulum


def process_level(item):
    """
    hideout level 가공
    """
    id = item.get("id")
    level = item.get("level")
    construction_time = item.get("constructionTime")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id, level, construction_time, update_time
    )
