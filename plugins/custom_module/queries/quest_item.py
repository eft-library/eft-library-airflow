"""SQL for quest item. Execution and transactions belong to the caller."""


INSERT_ITEMS = """
                insert into items (
                    id, parent_category, category, name_en, name_ko, name_ja, normalized_name, weight, width, height, image
                ) values %s
                on conflict (id) do update set
                    parent_category=excluded.parent_category,
                    category=excluded.category,
                    name_en=excluded.name_en,
                    normalized_name=excluded.normalized_name,
                    weight=excluded.weight,
                    width=excluded.width,
                    height=excluded.height,
                    image=excluded.image,
                    update_time=now()
        """


SELECT_ITEMS = "select id, normalized_name from items where normalized_name is not null"


INITIAL_INSERT_ITEMS = """
                insert into items (
                    id, parent_category, category, name_en, name_ko, name_ja, normalized_name, weight, width, height, image
                ) values %s
                on conflict (id) do update set
                    parent_category=excluded.parent_category,
                    category=excluded.category,
                    name_en=excluded.name_en,
                    name_ko=excluded.name_ko,
                    name_ja=excluded.name_ja,
                    normalized_name=excluded.normalized_name,
                    weight=excluded.weight,
                    width=excluded.width,
                    height=excluded.height,
                    image=excluded.image,
                    update_time=now()
        """
