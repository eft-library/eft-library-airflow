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
    return (
        id, name_en, image, construction_time, level_ids, update_time
    )


def get_level_ids(levels):
    """
    level id list 추출
    """
    level_ids = []
    print(levels)
    print(len(levels))
    for level in levels:
        print(level["id"], level)
        level_ids.append(level["id"])

    return level_ids