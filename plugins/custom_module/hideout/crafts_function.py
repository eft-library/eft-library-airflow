import pendulum

def process_crafts(item):
    """
    hideout crafts 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    id = item.get("id")
    station_id = item['station'].get("id") if item.get("station") else None
    level = item.get("level")
    name_en = get_name_list(item.get("rewardItems"))

    return (
        id, f"{station_id}-{level}", level, name_en, update_time
    )


def get_name_list(rewards):
    """
    보상 리스트로 뽑기
    """
    reward_list = []

    for reward in rewards:
        reward_list.append(reward["item"].get("name"))

    return reward_list