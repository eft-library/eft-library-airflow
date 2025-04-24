import json
import pendulum
from collections import defaultdict


def v2_key_process(item_en, item_ko, item_ja, en_key_map, ko_key_map, ja_key_map):
    """
    key 데이터 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    url_mapping = item_en.get("normalizedName")
    category = "Key"
    weight = item_en.get("weight")
    properties = item_en.get("properties") or {}
    uses = properties.get("uses")

    info = json.dumps(
        {
            "use_map": {
                "en": en_key_map.get(item_id),
                "ko": ko_key_map.get(item_id),
                "ja": ja_key_map.get(item_id),
            },
            "weight": weight,
            "uses": uses,
        }
    )
    image = item_en.get("gridImageLink")
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
        url_mapping,
        update_time,
    )


def process_key_map(item_list):
    key_map = defaultdict(set)

    for map_data in item_list:
        map_name = map_data.get("name")
        for key_data in map_data.get("locks", []):
            key_name = key_data.get("key", {}).get("id")
            if key_name:
                key_map[key_name].add(map_name)

    return {k: list(v) for k, v in key_map.items()}
