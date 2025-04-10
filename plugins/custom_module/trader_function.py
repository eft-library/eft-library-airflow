import json
import pendulum

trader_graphql = """
{
  traders {
    id
    name
    imageLink
    barters {
      level
      requiredItems {
        item {
          id
          name
          gridImageLink
        }
        quantity
      }
      rewardItems {
        item {
          id
          name
          gridImageLink
        }
        quantity
      }
    }
  }
}
"""


def process_trader(item):
    """
    trader 가공
    """
    npc_id = item.get("id")
    name = item.get("name")
    trader_image = item.get("imageLink")
    barter_info =  json.dumps(item.get("barters"))
    update_time = pendulum.now("Asia/Seoul")

    return (npc_id, name, trader_image, barter_info, update_time)