import pendulum


def process_item_require(level_id, item):
    """
    hideout item_require 가공
    """
    update_time = pendulum.now("Asia/Seoul")
    id = item.get("id")
    name_en = item['item'].get('name') if item.get("item") else None
    image = item['item'].get('image512pxLink') if item.get("item") else None
    quantity = item.get("quantity")
    count = item.get("count")
    return (
        id, level_id, name_en, quantity, count, image, update_time
    )
