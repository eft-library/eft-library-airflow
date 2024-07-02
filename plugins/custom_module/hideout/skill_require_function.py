import pendulum


def process_skill_require(level_id, item):
    """
    hideout skill require 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    id = item.get("id")
    level = item.get('level')
    name_en = item['skill'].get('name') if item.get("skill") else None
    return (
        id, level_id, level, name_en, update_time
    )
