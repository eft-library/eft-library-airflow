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
    리스트 형태이지만 하나 밖에 없음
    """
    if len(rewards) > 1:
        return rewards[0]["item"].get("name")
    return None