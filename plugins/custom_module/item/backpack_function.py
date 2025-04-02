import json
import pendulum

def new_process_backpack(item):
    """
    backpack 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Backpack"
    turn_penalty = item["properties"].get("turnPenalty") if item.get("properties") else None
    ergo_penalty = item["properties"].get("ergoPenalty") if item.get("properties") else None
    speed_penalty = item["properties"].get("speedPenalty") if item.get("properties") else None
    info = json.dumps({"weight": item.get("weight"),
                       "capacity": item["properties"].get("capacity"),
                       "turn_penalty": turn_penalty,
                       "ergo_penalty": ergo_penalty,
                       "speed_penalty": speed_penalty,
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