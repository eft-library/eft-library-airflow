import pendulum


def process_arm_band(item):
    """
    arm_band 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("gridImageLink")
    weight = item.get("weight")
    width = item.get("width")
    height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        weight,
        image,
        width,
        height,
        update_time,
    )