import pendulum


def process_loot(item):
    """
    loot 데이터 가공
    """

    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    category = item["category"].get("name") if item.get("category") else None
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        category,
        update_time,
    )