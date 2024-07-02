import pendulum


def process_station_require(level_id, item):
    """
    hideout station_require 가공
    """
    id = item.get("id")
    level = item.get("level")
    name_en = item['station'].get('name') if item.get("station") else None
    image = item['station'].get('imageLink') if item.get("station") else None
    update_time = pendulum.now("Asia/Seoul")

    return (
        id, level_id, level, name_en, image, update_time
    )
