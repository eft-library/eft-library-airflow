import json
import pendulum

quest_graphql = """
{
  tasks {
    id
    name
    trader {
      name
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
      ... on TaskObjectiveQuestItem {
        id
        type
        questItem {
          id
          name
          shortName
          description
        }
        count
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
    name = quest.get("name")
    npc_name = (
        quest.get("trader").get("name") if quest.get("trader").get("name") else None
    )
    task_requirements = json.dumps(quest.get("taskRequirements"))
    objectives = json.dumps(quest.get("objectives"))
    update_time = pendulum.now("Asia/Seoul")

    return (id, name, npc_name, task_requirements, objectives, update_time)
