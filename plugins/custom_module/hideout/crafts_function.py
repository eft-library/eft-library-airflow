import pendulum

def process_crafts(item):
    """
    hideout crafts 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    id = item.get("id")
    station_id = item['station'].get("id") if item.get("station") else None
    level = item.get("level")
    name_en = get_name(item.get("rewardItems"))

    return (
        id, f"{station_id}-{level}", level, name_en, update_time
    )


def get_name(rewards):
    """
    보상 뽑기
    리스트지만 데이터 하나임
    """
    for reward in rewards:
        return reward["item"].get("name")
    return None