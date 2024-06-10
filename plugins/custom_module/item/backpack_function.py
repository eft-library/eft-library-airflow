import pendulum

def process_backpack(item):
    """
    back 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    weight = item.get("weight")
    image = item.get("image512pxLink")
    grids = item["properties"].get("grids")
    capacity = item["properties"].get("capacity")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        weight,
        image,
        grids,
        capacity,
        update_time,
    )