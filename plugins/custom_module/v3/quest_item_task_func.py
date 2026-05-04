def generate_quest_item_graphql(lang: str) -> str:
    return f"""
{{
  questItems(lang: {lang}) {{
    id
    name
    normalizedName
    width
    height
    gridImageLink
  }}
}}
"""


def v3_quest_item_process(item_en, item_ko, item_ja):
    item_ko = item_ko or {}
    item_ja = item_ja or {}
    item_id = item_en.get("id")
    normalized_name = item_en.get("normalizedName")
    name_en = item_en.get("name")
    name_ko = item_ko.get("name")
    name_ja = item_ja.get("name")
    weight = 0
    category = "Loot"
    parent_category = "Quest Item"
    image = item_en.get("gridImageLink")
    image_width = item_en.get("width")
    image_height = item_en.get("height")

    return (
        item_id,
        parent_category,
        category,
        name_en,
        name_ko,
        name_ja,
        normalized_name,
        weight,
        image_width,
        image_height,
        image,
    )
