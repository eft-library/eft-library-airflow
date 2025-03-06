import pendulum


def process_throwable(item):
    """
    throwable 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    category = item["category"].get("name") if item.get("category") else None
    fuse = item["properties"].get("fuse") if item.get("properties") else None
    min_explosion_distance = (
        item["properties"].get("minExplosionDistance")
        if item.get("properties")
        else None
    )
    max_explosion_distance = (
        item["properties"].get("maxExplosionDistance")
        if item.get("properties")
        else None
    )
    fragments = item["properties"].get("fragments") if item.get("properties") else None
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        category,
        fuse,
        min_explosion_distance,
        max_explosion_distance,
        fragments,
        update_time,
    )