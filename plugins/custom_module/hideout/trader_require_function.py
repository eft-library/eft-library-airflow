import pendulum


def process_trader_require(level_id, item):
    """
    hideout trader 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    id = item.get("id")
    value = item.get("value")
    compare = item.get("compareMethod")
    require_type = item.get("requirementType")
    image = item['trader'].get('imageLink') if item.get("trader") else None
    name_en = item['trader'].get('name') if item.get("trader") else None
    return (
        id, level_id, name_en, value, require_type, compare, image, update_time
    )
