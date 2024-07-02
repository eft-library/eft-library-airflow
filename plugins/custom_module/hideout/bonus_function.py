import pendulum


def process_bonus(level_id, item):
    """
    hideout bonus 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    type = item.get("type")
    name_en = item.get("name")
    value = item.get("value")
    skill_name_en = item.get("skillName")
    return (
        id, level_id, type, name_en, value, skill_name_en, update_time
    )

