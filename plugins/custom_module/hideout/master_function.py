import pendulum


def process_master(item):
    """
    hideout master 가공
    """
    id = item.get("id")
    name_en = item.get('name')
    image = item.get("imageLink")
    construction_time = item.get("constructionTime")
    level_ids = get_level_ids(item.get("levels"))
    update_time = pendulum.now("Asia/Seoul")
    print(item)
    return (
        id, name_en, image, construction_time, level_ids, update_time
    )


def get_level_ids(levels):
    """
    level id list 추출
    """
    print(levels)
    level_ids = []

    for level in levels:
        level_ids.append(level.get("id"))

    return level_ids