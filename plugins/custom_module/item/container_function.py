import json
import pendulum

def new_process_container(item):
    """
    container 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Container"
    info = json.dumps({"width": item.get("width"),
                       "height": item.get("height"),
                       "capacity": item["properties"].get("capacity"),
                       "grids": item["properties"].get("grids")})
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