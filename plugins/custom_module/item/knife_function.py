import pendulum


def process_knife(item):
    """
    knife 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    category = item["category"].get("name") if item.get("category") else None
    slash_damage = (
        item["properties"].get("slashDamage") if item.get("properties") else None
    )
    stab_damage = (
        item["properties"].get("stabDamage") if item.get("properties") else None
    )
    hit_radius = item["properties"].get("hitRadius") if item.get("properties") else None
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        category,
        slash_damage,
        stab_damage,
        hit_radius,
        update_time,
    )