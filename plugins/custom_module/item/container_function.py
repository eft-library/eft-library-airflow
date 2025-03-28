import json
import pendulum

def process_container(item):
    """
    container 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("gridImageLink")
    grids = json.dumps(item["properties"].get("grids"))
    capacity = item["properties"].get("capacity")
    width = item.get("width")
    height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        grids,
        capacity,
        width,
        height,
        update_time,
    )

def new_process_container(item):
    """
    container 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Container"
    info = json.dumps({"width": item.get("width"), "height": item.get("height"), "capacity": item["properties"].get("capacity"), "grids": item["properties"].get("grids")})
    image = item.get("gridImageLink")
    image_width = item.get("width")
    image_height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")

    return (
        item_id,
        name_en,
        category,
        info,
        image,
        image_width,
        image_height,
        update_time
    )