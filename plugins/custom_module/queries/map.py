"""SQL for map. Execution and transactions belong to the caller."""


SELECT_MAPS = """
                    select id, name_en, normalized_name
                    from maps
                    """


INSERT_MAPS = """
            INSERT INTO maps (
                id,
                normalized_name,
                name_en,
                name_ko,
                name_ja
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en
        """


INITIAL_INSERT_MAPS = """
            INSERT INTO maps (
                id,
                normalized_name,
                name_en,
                name_ko,
                name_ja
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja
        """
