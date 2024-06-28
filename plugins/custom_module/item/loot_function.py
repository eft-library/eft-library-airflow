import pendulum


def process_loot(item):
    """
    loot 데이터 가공
    """

    id = item.get("id")
    name_en = item.get("name")
    name_kr = get_loot_kr(name_en)
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    category = item["category"].get("name") if item.get("category") else None
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name_en,
        name_kr,
        short_name,
        image,
        category,
        update_time,
    )


def get_loot_kr(name):
    """
    전리품 한글 이름
    """

    return name
