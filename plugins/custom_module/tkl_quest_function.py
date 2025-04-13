import json
import pendulum

quest_graphql = """
{
  tasks {
    id
    name
    kappaRequired
    lightkeeperRequired
    trader {
      id
    }
    taskRequirements{
      task {
        id
        name
      }
    }
    objectives {
      id
      type
      description
      ... on TaskObjectiveQuestItem {
        questItem {
          id
          name
          gridImageLink
        }
        count
      }
      ... on TaskObjectiveItem {
        items {
          id
          name
          gridImageLink
        }
        count
        foundInRaid
      }
    }
    finishRewards {
      items {
        item {
          id
          name
          gridImageLink
        }
        count
        quantity
      }
    }
  }
}
"""


def process_quest(quest):
    """
    quest 가공
    """
    id = quest.get("id")
    name_en = quest.get("name")
    npc_id = (
        quest.get("trader").get("id") if quest.get("trader").get("id") else None
    )
    lightkeeper_required = quest.get("lightkeeperRequired")
    kappa_required = quest.get("kappaRequired")
    task_requirements = json.dumps(quest.get("taskRequirements"))
    objectives = json.dumps(quest.get("objectives"))
    finish_rewards = quest.get("finishRewards")
    update_time = pendulum.now("Asia/Seoul")

    return (id, name_en, npc_id, lightkeeper_required, kappa_required, task_requirements, objectives, finish_rewards, update_time)
