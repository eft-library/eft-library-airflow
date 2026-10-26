"""SQL for map of tarkov. Execution and transactions belong to the caller."""


SELECT_MAPS = """
                select normalized_name
                from maps
                where is_use is true
                  and normalized_name is not null
                order by sort_order, name_en, normalized_name;
                """
