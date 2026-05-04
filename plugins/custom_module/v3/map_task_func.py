def generate_map_graphql(lang: str):
    return f"""
{{
  maps(lang: {lang}) {{
    id
    name
    normalizedName
  }}
}}
"""


def v3_map_process(item_en, item_ko, item_ja):
    item_ko = item_ko or {}
    item_ja = item_ja or {}
    map_id = item_en.get("id")
    name_en = item_en.get("name")
    name_ko = item_ko.get("name")
    name_ja = item_ja.get("name")
    normalized_name = item_en.get("normalizedName")

    return (map_id, normalized_name, name_en, name_ko, name_ja)
