import pendulum

quest_item_graphql = """
{
  questItems {
    id
    name
    image512pxLink
  }
}
"""

def process_quest_item(item):
    """
    loot에 들어가는 quest item 데이터 가공
    """

    id = item.get("id")
    name_en = item.get("name")
    image = item.get("image512pxLink")
    category = "Quest items"
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name_en,
        image,
        category,
        update_time,
    )

