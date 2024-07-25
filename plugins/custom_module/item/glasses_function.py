import pendulum


def process_glasses(item):
    """
    glasses 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    class_value = None
    durability = None
    blindness_protection = None
    update_time = pendulum.now("Asia/Seoul")

    if item["properties"]["class"] is not None:
        class_value = item["properties"].get("class")
        durability = item["properties"].get("durability")
        blindness_protection = item["properties"].get("blindnessProtection")

    return (
        id,
        name,
        short_name,
        class_value,
        durability,
        blindness_protection,
        image,
        update_time,
    )