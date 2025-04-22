import json
import pendulum


def generate_quest_item_graphql(lang: str) -> str:
    return f"""
{{
  questItems(lang: {lang}) {{
    id
    name
    width
    height
    gridImageLink
  }}
}}
"""


def v2_quest_item_process(item_en, item_ko, item_ja):
    """
    quest item 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    category = "Loot"
    image = item_en.get("gridImageLink")
    info = json.dumps({"loot_category": "Quest items"})
    image_width = item_en.get("width")
    image_height = item_en.get("height")
    update_time = pendulum.now("Asia/Seoul")

    return (
        item_id,
        json.dumps(name),
        category,
        info,
        image,
        image_width,
        image_height,
        update_time,
    )
