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