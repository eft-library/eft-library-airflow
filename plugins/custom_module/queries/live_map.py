"""SQL for live map. Execution and transactions belong to the caller."""


SELECT_MAPS = """
                select m.normalized_name
                from maps m
                         join live_map_floors lmf on lmf.map_id = m.id
                where m.normalized_name is not null
                group by m.id, m.normalized_name, m.sort_order, m.name_en
                order by m.sort_order, m.name_en, m.normalized_name;
                """


SELECT_QUESTS = """
                select q.normalized_name
                from quests q
                where q.is_use is true
                  and q.normalized_name is not null
                  and exists (
                      select 1
                      from live_map_points lmp
                      where lmp.quest_id = q.id
                  )
                order by q.sort_order, q.name_en, q.normalized_name;
                """


SELECT_STORY = """
                select s.id
                from story s
                where exists (
                          select 1
                          from live_map_story_points lmsp
                          where lmsp.story_id = s.id
                      )
                   or exists (
                          select 1
                          from live_map_story_requirement_points lmsrp
                          where lmsrp.story_id = s.id
                      )
                order by s.sort_order, s.title_en, s.id;
                """


SELECT_LIVE_MAP_EVENTS = """
                select e.id
                from live_map_events e
                where e.is_active is true
                  and exists (
                      select 1
                      from live_map_event_points lmep
                      where lmep.event_id = e.id
                  )
                order by e.sort_order, e.title_en, e.id;
                """
