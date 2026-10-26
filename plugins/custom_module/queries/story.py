"""SQL for story. Execution and transactions belong to the caller."""


SELECT_STORY = """
                select id
                from story
                order by sort_order, title_en, id;
                """
