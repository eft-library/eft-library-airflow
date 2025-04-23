import json

import pendulum


def v2_hideout_master_process(item_en, item_ko, item_ja):
    """
    hideout master 가공
    """
    item_id = item_en.get("id")
    name = {
        "en": item_en.get("name"),
        "ko": item_ko.get("name"),
        "ja": item_ja.get("name"),
    }
    level_ids = get_level_ids(item_en.get("levels"))
    update_time = pendulum.now("Asia/Seoul")

    return (item_id, json.dumps(name), level_ids, update_time)


def get_level_ids(levels):
    """
    level id list 추출
    """
    level_ids = []
    for level in levels:
        level_ids.append(level["id"])

    return level_ids
