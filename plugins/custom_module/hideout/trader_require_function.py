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
    name_en = item['item'].get('name') if item.get("item") else None
    return (
        id, level_id, name_en, value, require_type, compare, update_time
    )
