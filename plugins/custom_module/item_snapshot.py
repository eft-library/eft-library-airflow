"""Live item/category collection from json.tarkov.dev; no local fixture fallback."""
import copy

from custom_module import tarkov_json_api as api
from custom_module.weapon_modding import build_modding_rows


def get_item_snapshot(game_mode="regular"):
    """Fetch one authoritative item/category payload plus localization dictionaries."""

    data = api._request_json(f"{game_mode}/items")["data"]
    build_modding_rows(data)  # Reject partial snapshots before publishing task files.
    translations = {
        lang: api._request_json(f"{game_mode}/items_{lang}")["data"]
        for lang in ("en", "ko", "ja")
    }
    localized = api._translate(data, translations["en"])
    categories = localized["itemCategories"]
    items = []
    for raw_item in localized["items"].values():
        item = copy.deepcopy(raw_item)
        item["category"] = api._category_data(item, categories)
        item["properties"] = api._item_properties(item.get("properties"))
        items.append(item)
    names = {}
    for lang in ("ko", "ja"):
        names[lang] = {}
        for item_id, item in data["items"].items():
            name = translations[lang].get(item.get("name"))
            if isinstance(name, str) and name.strip():
                names[lang][item_id] = {"name": name}
    return {"data": data, "translations": translations, "items": items, "names": names,
            "game_mode": game_mode}
