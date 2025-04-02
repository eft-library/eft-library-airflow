import json

import pendulum

quest_item_graphql = """
{
  questItems {
    id
    name
    image512pxLink
    width
    height
    gridImageLink
  }
}
"""

def new_process_quest_item(item):
    """
    quest item 데이터 가공
    """
    item_id = item.get("id")
    name_en = item.get("name")
    category = "Loot"
    image = item.get("gridImageLink")
    info = json.dumps({"loot_category": "Quest items"})
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
        update_time,
    )

