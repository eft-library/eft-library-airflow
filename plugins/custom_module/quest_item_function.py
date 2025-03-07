import pendulum

quest_item_graphql = """
{
  questItems {
    id
    name
    image512pxLink
    width
    height
    gridImageLink
  }
}
"""

def process_quest_item(item):
    """
    loot에 들어가는 quest item 데이터 가공
    """

    id = item.get("id")
    name_en = item.get("name")
    image = item.get("gridImageLink")
    category = "Quest items"
    width = item.get("width")
    height = item.get("height")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name_en,
        image,
        category,
        width,
        height,
        update_time,
    )

