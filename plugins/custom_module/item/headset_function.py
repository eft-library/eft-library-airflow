import pendulum


def process_headset(item):
    """
    headset 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        update_time,
    )