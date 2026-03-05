"""
item_i18n + item_detail_i18n + hideout_crafts_i18n 배치 임베딩 - Airflow DAG 태스크용
- item_i18n + item_detail_i18n joined
- hideout_crafts_i18n 제작 레시피 추가
- 카테고리별 info 파서 분리
- asyncio 동시 처리 (CONCURRENT_LIMIT)
- 이미 처리된 아이템 스킵 (재시작 안전)
- bge-m3로 임베딩 생성
- rag_documents 테이블에 upsert

청크 분리:
  - item_id        : 이름 + 카테고리 (chunk_type: identifier) → RDB 조회용
  - item_id_spec   : 카테고리별 스펙 (chunk_type: content)
  - item_id_detail : hideout 건설, 퀘스트, NPC 교환 등 (chunk_type: content)
  - item_id_craft  : 제작 레시피 (chunk_type: content)
"""

import asyncio
import httpx
import json
import logging
from contextlib import closing
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import Variable

OLLAMA_BASE_URL = Variable.get("OLLAMA_BASE_URL")
EMBED_MODEL = Variable.get("OLLAMA_EMBED_MODEL")
BATCH_SIZE = 50
CONCURRENT_LIMIT = 5
SKIP_EXISTING = False
LANGS = ["ko", "en", "ja"]

log = logging.getLogger(__name__)


# ── 유틸
def get_lang_value(jsonb_field: dict | str | None, lang: str) -> str:
    if not jsonb_field:
        return ""
    if isinstance(jsonb_field, str):
        try:
            jsonb_field = json.loads(jsonb_field)
        except json.JSONDecodeError:
            return ""
    return jsonb_field.get(lang, "") or ""


def parse_jsonb(value) -> list | dict | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


def fmt(value, suffix="") -> str:
    if value is None:
        return ""
    return f"{value}{suffix}"


# ── 카테고리별 info 파서
def parse_ammo(info: dict, lang: str) -> str:
    label = {
        "ko": "데미지: {damage} | 관통력: {pen} | 장갑 데미지: {ad}%\n반동 보정: {rec} | 명중률 보정: {acc}",
        "en": "Damage: {damage} | Penetration: {pen} | Armor Damage: {ad}%\nRecoil: {rec} | Accuracy: {acc}",
        "ja": "ダメージ: {damage} | 貫通力: {pen} | アーマーダメージ: {ad}%\n反動補正: {rec} | 命中補正: {acc}",
    }[lang]
    return label.format(
        damage=fmt(info.get("damage")),
        pen=fmt(info.get("penetration_power")),
        ad=fmt(info.get("armor_damage")),
        rec=fmt(info.get("recoil_modifier")),
        acc=fmt(info.get("accuracy_modifier")),
    )


def parse_armor(info: dict, lang: str) -> str:
    zones_key = f"zones_{lang}"
    zones = (info.get("zones") or {}).get(zones_key, [])
    zone_str = ", ".join(zones) if zones else ""
    return {
        "ko": f"방어 등급: {fmt(info.get('class_value'))} | 내구도: {fmt(info.get('durability'))} | 무게: {fmt(info.get('weight'))}kg\n재질: {fmt((info.get('material') or {}).get('name'))}\n방어 부위: {zone_str}",
        "en": f"Class: {fmt(info.get('class_value'))} | Durability: {fmt(info.get('durability'))} | Weight: {fmt(info.get('weight'))}kg\nMaterial: {fmt((info.get('material') or {}).get('name'))}\nZones: {zone_str}",
        "ja": f"防護クラス: {fmt(info.get('class_value'))} | 耐久度: {fmt(info.get('durability'))} | 重量: {fmt(info.get('weight'))}kg\n素材: {fmt((info.get('material') or {}).get('name'))}\n防護部位: {zone_str}",
    }[lang]


def parse_gun(info: dict, lang: str) -> str:
    modes_key = f"modes_{lang}"
    modes = (info.get("modes") or {}).get(modes_key, [])
    modes_str = ", ".join(modes) if modes else ""
    allowed = info.get("allowed_ammo") or []
    ammo_str = ", ".join(a.get("name", "") for a in allowed[:5])
    if len(allowed) > 5:
        ammo_str += f" 외 {len(allowed)-5}종"
    return {
        "ko": f"종류: {fmt(info.get('gun_category'))} | 구경: {fmt(info.get('caliber'))} | 무게: {fmt(info.get('weight'))}kg\n발사 속도: {fmt(info.get('fire_rate'))}rpm | 발사 모드: {modes_str}\n기본 탄약: {fmt(info.get('default_ammo'))}\n사용 가능 탄약: {ammo_str}",
        "en": f"Type: {fmt(info.get('gun_category'))} | Caliber: {fmt(info.get('caliber'))} | Weight: {fmt(info.get('weight'))}kg\nFire Rate: {fmt(info.get('fire_rate'))}rpm | Modes: {modes_str}\nDefault Ammo: {fmt(info.get('default_ammo'))}\nAllowed Ammo: {ammo_str}",
        "ja": f"種類: {fmt(info.get('gun_category'))} | 口径: {fmt(info.get('caliber'))} | 重量: {fmt(info.get('weight'))}kg\n発射速度: {fmt(info.get('fire_rate'))}rpm | 発射モード: {modes_str}\nデフォルト弾薬: {fmt(info.get('default_ammo'))}\n使用可能弾薬: {ammo_str}",
    }[lang]


def parse_medical(info: dict, lang: str) -> str:
    cures = (info.get("cures") or {}).get(lang, [])
    cures_str = ", ".join(cures) if cures else ""
    buff = info.get("buff") or []
    malus = info.get("malus") or []
    skill_key = f"skill_name_{lang}"
    buff_str = ", ".join(
        f"{b.get(skill_key, b.get('type', ''))} +{b.get('value')} ({b.get('duration')}초)"
        for b in buff
        if b.get("value")
    )
    malus_str = ", ".join(
        f"{m.get(skill_key, m.get('type', ''))} ({m.get('duration')}초)" for m in malus
    )
    return {
        "ko": f"종류: {fmt(info.get('medical_category'))} | 무게: {fmt(info.get('weight'))}kg | 사용 횟수: {fmt(info.get('uses'))}\n치료 효과: {cures_str}\n버프: {buff_str}\n디버프: {malus_str}",
        "en": f"Type: {fmt(info.get('medical_category'))} | Weight: {fmt(info.get('weight'))}kg | Uses: {fmt(info.get('uses'))}\nCures: {cures_str}\nBuff: {buff_str}\nDebuff: {malus_str}",
        "ja": f"種類: {fmt(info.get('medical_category'))} | 重量: {fmt(info.get('weight'))}kg | 使用回数: {fmt(info.get('uses'))}\n治療効果: {cures_str}\nバフ: {buff_str}\nデバフ: {malus_str}",
    }[lang]


def parse_key(info: dict, lang: str) -> str:
    use_map = (info.get("use_map") or {}).get(lang, []) or []
    map_str = ", ".join(use_map) if use_map else ""
    return {
        "ko": f"사용 횟수: {fmt(info.get('uses'))} | 무게: {fmt(info.get('weight'))}kg\n사용 지도: {map_str}",
        "en": f"Uses: {fmt(info.get('uses'))} | Weight: {fmt(info.get('weight'))}kg\nUsable Map: {map_str}",
        "ja": f"使用回数: {fmt(info.get('uses'))} | 重量: {fmt(info.get('weight'))}kg\n使用マップ: {map_str}",
    }[lang]


def parse_backpack(info: dict, lang: str) -> str:
    return {
        "ko": f"용량: {fmt(info.get('capacity'))}칸 | 무게: {fmt(info.get('weight'))}kg\n이동 패널티: {fmt(info.get('speed_penalty'))} | 인체공학 패널티: {fmt(info.get('ergo_penalty'))}",
        "en": f"Capacity: {fmt(info.get('capacity'))} | Weight: {fmt(info.get('weight'))}kg\nSpeed Penalty: {fmt(info.get('speed_penalty'))} | Ergo Penalty: {fmt(info.get('ergo_penalty'))}",
        "ja": f"容量: {fmt(info.get('capacity'))} | 重量: {fmt(info.get('weight'))}kg\n移動ペナルティ: {fmt(info.get('speed_penalty'))} | エルゴペナルティ: {fmt(info.get('ergo_penalty'))}",
    }[lang]


def parse_rig(info: dict, lang: str) -> str:
    zones_key = f"zones_{lang}"
    zones = (info.get("zones") or {}).get(zones_key, [])
    zone_str = ", ".join(zones) if zones else ""
    return {
        "ko": f"용량: {fmt(info.get('capacity'))}칸 | 방어 등급: {fmt(info.get('class_value'))} | 내구도: {fmt(info.get('durability'))}\n무게: {fmt(info.get('weight'))}kg | 방어 부위: {zone_str}",
        "en": f"Capacity: {fmt(info.get('capacity'))} | Class: {fmt(info.get('class_value'))} | Durability: {fmt(info.get('durability'))}\nWeight: {fmt(info.get('weight'))}kg | Zones: {zone_str}",
        "ja": f"容量: {fmt(info.get('capacity'))} | 防護クラス: {fmt(info.get('class_value'))} | 耐久度: {fmt(info.get('durability'))}\n重量: {fmt(info.get('weight'))}kg | 防護部位: {zone_str}",
    }[lang]


def parse_headwear(info: dict, lang: str) -> str:
    zones_key = f"zones_{lang}"
    zones = (info.get("zones") or {}).get(zones_key, [])
    ricochet_key = f"ricochet_chance_{lang}"
    ricochet = (info.get("ricochet_chance") or {}).get(ricochet_key, "")
    return {
        "ko": f"방어 등급: {fmt(info.get('class_value'))} | 내구도: {fmt(info.get('durability'))} | 무게: {fmt(info.get('weight'))}kg\n재질: {fmt((info.get('material') or {}).get('name'))} | 도탄 확률: {ricochet}\n방어 부위: {', '.join(zones)}",
        "en": f"Class: {fmt(info.get('class_value'))} | Durability: {fmt(info.get('durability'))} | Weight: {fmt(info.get('weight'))}kg\nMaterial: {fmt((info.get('material') or {}).get('name'))} | Ricochet: {ricochet}\nZones: {', '.join(zones)}",
        "ja": f"防護クラス: {fmt(info.get('class_value'))} | 耐久度: {fmt(info.get('durability'))} | 重量: {fmt(info.get('weight'))}kg\n素材: {fmt((info.get('material') or {}).get('name'))} | 跳弾確率: {ricochet}\n防護部位: {', '.join(zones)}",
    }[lang]


def parse_facecover(info: dict, lang: str) -> str:
    zones_key = f"zones_{lang}"
    zones = (info.get("zones") or {}).get(zones_key, [])
    ricochet_key = f"ricochet_chance_{lang}"
    ricochet = (info.get("ricochet_chance") or {}).get(ricochet_key, "")
    return {
        "ko": f"방어 등급: {fmt(info.get('class_value'))} | 내구도: {fmt(info.get('durability'))} | 무게: {fmt(info.get('weight'))}kg\n도탄 확률: {ricochet} | 방어 부위: {', '.join(zones)}",
        "en": f"Class: {fmt(info.get('class_value'))} | Durability: {fmt(info.get('durability'))} | Weight: {fmt(info.get('weight'))}kg\nRicochet: {ricochet} | Zones: {', '.join(zones)}",
        "ja": f"防護クラス: {fmt(info.get('class_value'))} | 耐久度: {fmt(info.get('durability'))} | 重量: {fmt(info.get('weight'))}kg\n跳弾確率: {ricochet} | 防護部位: {', '.join(zones)}",
    }[lang]


def parse_throwable(info: dict, lang: str) -> str:
    return {
        "ko": f"무게: {fmt(info.get('weight'))}kg | 퓨즈: {fmt(info.get('fuse'))}초\n파편: {fmt(info.get('fragments'))}개 | 폭발 범위: {fmt(info.get('min_explosion_distance'))}~{fmt(info.get('max_explosion_distance'))}m",
        "en": f"Weight: {fmt(info.get('weight'))}kg | Fuse: {fmt(info.get('fuse'))}s\nFragments: {fmt(info.get('fragments'))} | Blast Radius: {fmt(info.get('min_explosion_distance'))}~{fmt(info.get('max_explosion_distance'))}m",
        "ja": f"重量: {fmt(info.get('weight'))}kg | 信管: {fmt(info.get('fuse'))}秒\n破片: {fmt(info.get('fragments'))}個 | 爆発範囲: {fmt(info.get('min_explosion_distance'))}~{fmt(info.get('max_explosion_distance'))}m",
    }[lang]


def parse_provisions(info: dict, lang: str) -> str:
    return {
        "ko": f"무게: {fmt(info.get('weight'))}kg | 에너지: {fmt(info.get('energy'))} | 수분: {fmt(info.get('hydration'))}",
        "en": f"Weight: {fmt(info.get('weight'))}kg | Energy: {fmt(info.get('energy'))} | Hydration: {fmt(info.get('hydration'))}",
        "ja": f"重量: {fmt(info.get('weight'))}kg | エネルギー: {fmt(info.get('energy'))} | 水分: {fmt(info.get('hydration'))}",
    }[lang]


def parse_loot(info: dict, lang: str) -> str:
    return {
        "ko": f"무게: {fmt(info.get('weight'))}kg | 카테고리: {fmt(info.get('loot_category'))}",
        "en": f"Weight: {fmt(info.get('weight'))}kg | Category: {fmt(info.get('loot_category'))}",
        "ja": f"重量: {fmt(info.get('weight'))}kg | カテゴリ: {fmt(info.get('loot_category'))}",
    }[lang]


def parse_knife(info: dict, lang: str) -> str:
    return {
        "ko": f"무게: {fmt(info.get('weight'))}kg | 찌르기 데미지: {fmt(info.get('stab_damage'))} | 베기 데미지: {fmt(info.get('slash_damage'))}\n범위: {fmt(info.get('hit_radius'))}m",
        "en": f"Weight: {fmt(info.get('weight'))}kg | Stab: {fmt(info.get('stab_damage'))} | Slash: {fmt(info.get('slash_damage'))}\nRange: {fmt(info.get('hit_radius'))}m",
        "ja": f"重量: {fmt(info.get('weight'))}kg | 刺突ダメージ: {fmt(info.get('stab_damage'))} | 斬撃ダメージ: {fmt(info.get('slash_damage'))}\n射程: {fmt(info.get('hit_radius'))}m",
    }[lang]


def parse_headset(info: dict, lang: str) -> str:
    return {
        "ko": f"무게: {fmt(info.get('weight'))}kg | 거리 보정: {fmt(info.get('distance_modifier'))}",
        "en": f"Weight: {fmt(info.get('weight'))}kg | Distance Modifier: {fmt(info.get('distance_modifier'))}",
        "ja": f"重量: {fmt(info.get('weight'))}kg | 距離補正: {fmt(info.get('distance_modifier'))}",
    }[lang]


def parse_container(info: dict, lang: str) -> str:
    return {
        "ko": f"무게: {fmt(info.get('weight'))}kg | 용량: {fmt(info.get('capacity'))}칸 | 크기: {fmt(info.get('width'))}x{fmt(info.get('height'))}",
        "en": f"Weight: {fmt(info.get('weight'))}kg | Capacity: {fmt(info.get('capacity'))} | Size: {fmt(info.get('width'))}x{fmt(info.get('height'))}",
        "ja": f"重量: {fmt(info.get('weight'))}kg | 容量: {fmt(info.get('capacity'))} | サイズ: {fmt(info.get('width'))}x{fmt(info.get('height'))}",
    }[lang]


def parse_armband(info: dict, lang: str) -> str:
    return {
        "ko": f"무게: {fmt(info.get('weight'))}kg",
        "en": f"Weight: {fmt(info.get('weight'))}kg",
        "ja": f"重量: {fmt(info.get('weight'))}kg",
    }[lang]


def parse_glasses(info: dict, lang: str) -> str:
    return {
        "ko": f"방어 등급: {fmt(info.get('class_value'))} | 내구도: {fmt(info.get('durability'))} | 무게: {fmt(info.get('weight'))}kg\n실명 방어: {fmt(info.get('blindness_protection'))}",
        "en": f"Class: {fmt(info.get('class_value'))} | Durability: {fmt(info.get('durability'))} | Weight: {fmt(info.get('weight'))}kg\nBlindness Protection: {fmt(info.get('blindness_protection'))}",
        "ja": f"防護クラス: {fmt(info.get('class_value'))} | 耐久度: {fmt(info.get('durability'))} | 重量: {fmt(info.get('weight'))}kg\n盲目防御: {fmt(info.get('blindness_protection'))}",
    }[lang]


def parse_default(info: dict, lang: str) -> str:
    weight = info.get("weight")
    if not weight:
        return ""
    return {
        "ko": f"무게: {weight}kg",
        "en": f"Weight: {weight}kg",
        "ja": f"重量: {weight}kg",
    }[lang]


INFO_PARSERS = {
    "Ammo": parse_ammo,
    "ArmorVest": parse_armor,
    "Gun": parse_gun,
    "Medical": parse_medical,
    "Key": parse_key,
    "Backpack": parse_backpack,
    "Rig": parse_rig,
    "Headwear": parse_headwear,
    "FaceCover": parse_facecover,
    "Throwable": parse_throwable,
    "Provisions": parse_provisions,
    "Loot": parse_loot,
    "Knife": parse_knife,
    "Headset": parse_headset,
    "Container": parse_container,
    "Armband": parse_armband,
    "Glasses": parse_glasses,
    "Other": parse_default,
}


# ── 라벨
DETAIL_LABELS = {
    "ko": {
        "hideout": "은신처 건설 필요",
        "crafts": "이 아이템이 재료로 사용되는 제작",
        "npc": "상인 교환",
        "quest_reward": "퀘스트 보상",
        "quest_item": "퀘스트 제출 아이템",
        "craft_unlock": "제작 잠금해제 퀘스트",
        "offer_unlock": "구매 잠금해제 퀘스트",
        "lv": "레벨",
    },
    "en": {
        "hideout": "Required for Hideout",
        "crafts": "Used as material in",
        "npc": "Barter (NPC)",
        "quest_reward": "Quest Reward",
        "quest_item": "Quest Item",
        "craft_unlock": "Craft Unlock Quest",
        "offer_unlock": "Offer Unlock Quest",
        "lv": "Level",
    },
    "ja": {
        "hideout": "隠れ家建設に必要",
        "crafts": "このアイテムが素材として使われるクラフト",
        "npc": "商人交換",
        "quest_reward": "クエスト報酬",
        "quest_item": "クエストアイテム",
        "craft_unlock": "クラフト解放クエスト",
        "offer_unlock": "購入解放クエスト",
        "lv": "レベル",
    },
}

CRAFT_LABELS = {
    "ko": {
        "title": "이 아이템을 만드는 방법 (제작법)",
        "result": "결과물",
        "duration": "제작 시간",
        "required": "필요 재료",
        "min": "분",
        "hour": "시간",
    },
    "en": {
        "title": "How to craft this item",
        "result": "Result",
        "duration": "Duration",
        "required": "Required Items",
        "min": "min",
        "hour": "h",
    },
    "ja": {
        "title": "このアイテムの製作方法",
        "result": "結果",
        "duration": "製作時間",
        "required": "必要素材",
        "min": "分",
        "hour": "時間",
    },
}

CATEGORY_LABEL = {"ko": "카테고리", "en": "Category", "ja": "カテゴリ"}
SPEC_LABEL = {"ko": "스펙", "en": "Spec", "ja": "スペック"}
ITEM_LABEL = {"ko": "아이템", "en": "Item", "ja": "アイテム"}
NAME_KEY = {"ko": "name_ko", "en": "name_en", "ja": "name_ja"}


def format_duration(seconds: int, lang: str) -> str:
    lb = CRAFT_LABELS[lang]
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}{lb['min']}"
    hours = minutes // 60
    remaining = minutes % 60
    if remaining == 0:
        return f"{hours}{lb['hour']}"
    return f"{hours}{lb['hour']} {remaining}{lb['min']}"


# ── content 빌더
def build_identifier_content(item_row: dict, lang: str) -> str:
    name = get_lang_value(item_row["name"], lang)
    category = item_row.get("category") or ""
    return f"{ITEM_LABEL[lang]}: {name}\n{CATEGORY_LABEL[lang]}: {category}"


def build_spec_content(item_row: dict, lang: str) -> str:
    name = get_lang_value(item_row["name"], lang)
    category = item_row.get("category") or ""
    info = parse_jsonb(item_row.get("info")) or {}

    parser = INFO_PARSERS.get(category, parse_default)
    spec = parser(info, lang).strip()

    if not spec:
        return ""

    return "\n".join(
        [
            f"{ITEM_LABEL[lang]}: {name}",
            f"{CATEGORY_LABEL[lang]}: {category}",
            f"\n[{SPEC_LABEL[lang]}]\n{spec}",
        ]
    ).strip()


def build_detail_content(item_row: dict, detail_row: dict, lang: str) -> str:
    lb = DETAIL_LABELS[lang]
    nk = NAME_KEY[lang]
    name = get_lang_value(item_row["name"], lang)

    parts = [f"{ITEM_LABEL[lang]}: {name}"]
    detail_parts = []

    hideout = parse_jsonb(detail_row.get("hideout_items")) or []
    if hideout:
        lines = [
            f"- {get_lang_value(h.get('master_name'), lang)} {lb['lv']}{h.get('level', '')} x{h.get('count', '')}"
            for h in hideout
        ]
        detail_parts.append(f"[{lb['hideout']}]\n" + "\n".join(lines))

    crafts = parse_jsonb(detail_row.get("used_in_crafts")) or []
    if crafts:
        lines = [
            f"- {get_lang_value(c.get('name'), lang)} ({get_lang_value(c.get('master_name'), lang)} {lb['lv']}{c.get('level', '')})"
            for c in crafts
        ]
        detail_parts.append(f"[{lb['crafts']}]\n" + "\n".join(lines))

    npcs = parse_jsonb(detail_row.get("rewarded_by_npcs")) or []
    if npcs:
        lines = []
        for n in npcs:
            npc_name = get_lang_value(n.get("npc_name"), lang)
            barter = n.get("barter_info") or {}
            level = barter.get("level", "")
            req = barter.get("requiredItems") or []
            req_str = ", ".join(
                f"{r['item'].get(nk, '')} x{r.get('quantity', '')}"
                for r in req
                if r.get("item")
            )
            lines.append(f"- {npc_name} {lb['lv']}{level} | 필요: {req_str}")
        detail_parts.append(f"[{lb['npc']}]\n" + "\n".join(lines))

    quest_rewards = parse_jsonb(detail_row.get("rewarded_by_quests")) or []
    if quest_rewards:
        lines = [
            f"- {get_lang_value(q.get('name'), lang)} ({get_lang_value(q.get('npc_name'), lang)}) → x{(q.get('reward') or {}).get('quantity') or (q.get('reward') or {}).get('count', '')}"
            for q in quest_rewards
        ]
        detail_parts.append(f"[{lb['quest_reward']}]\n" + "\n".join(lines))

    quest_items = parse_jsonb(detail_row.get("required_by_quest_item")) or []
    if quest_items:
        lines = [
            f"- {get_lang_value(q.get('name'), lang)} ({get_lang_value(q.get('npc_name'), lang)}): {(q.get('objective') or {}).get(f'description_{lang}', '')}"
            for q in quest_items
        ]
        detail_parts.append(f"[{lb['quest_item']}]\n" + "\n".join(lines))

    craft_unlocks = parse_jsonb(detail_row.get("rewarded_by_quests_craft_unlock")) or []
    if craft_unlocks:
        lines = [
            f"- {get_lang_value(q.get('name'), lang)} ({get_lang_value(q.get('npc_name'), lang)}) → {(q.get('reward') or {}).get('trader', {}).get(nk, '')} {lb['lv']}{(q.get('reward') or {}).get('level', '')}"
            for q in craft_unlocks
        ]
        detail_parts.append(f"[{lb['craft_unlock']}]\n" + "\n".join(lines))

    offer_unlocks = parse_jsonb(detail_row.get("rewarded_by_quests_offer_unlock")) or []
    if offer_unlocks:
        lines = [
            f"- {get_lang_value(q.get('name'), lang)} ({get_lang_value(q.get('npc_name'), lang)}) → {(q.get('reward') or {}).get('trader', {}).get(nk, '')} {lb['lv']}{(q.get('reward') or {}).get('level', '')}"
            for q in offer_unlocks
        ]
        detail_parts.append(f"[{lb['offer_unlock']}]\n" + "\n".join(lines))

    if not detail_parts:
        return ""

    parts.append("\n" + "\n\n".join(detail_parts))
    return "\n".join(parts).strip()


def build_craft_content(item_row: dict, crafts: list[dict], lang: str) -> str:
    if not crafts:
        return ""

    lb = CRAFT_LABELS[lang]
    nk = NAME_KEY[lang]
    name = get_lang_value(item_row["name"], lang)

    lines = []
    for c in crafts:
        duration_sec = int(c.get("duration") or 0)
        duration_str = format_duration(duration_sec, lang)
        qty = c.get("quantity", 1)
        craft_name = get_lang_value(c.get("name"), lang)
        req_items = parse_jsonb(c.get("req_item")) or []
        req_str = "\n".join(
            f"  · {r['item'].get(nk, '')} x{r.get('quantity', 1)}"
            for r in req_items
            if r.get("item")
        )
        lines.append(
            f"{lb['result']}: {craft_name} x{qty}\n"
            f"{lb['duration']}: {duration_str}\n"
            f"{lb['required']}:\n{req_str}"
        )

    return "\n".join(
        [
            f"{ITEM_LABEL[lang]}: {name}",
            f"\n[{lb['title']}]\n" + "\n\n".join(lines),
        ]
    ).strip()


# ── 임베딩
async def get_embedding(client: httpx.AsyncClient, text: str) -> list[float]:
    response = await client.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


# ── upsert (psycopg2 cursor 사용)
def upsert_rag_document(
    cursor,
    source_id: str,
    lang: str,
    content: str,
    embedding: list[float],
    chunk_type: str,
    ref_type: str,
    ref_id: str,
    metadata: dict,
):
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    cursor.execute(
        """
        INSERT INTO rag_documents (
            source_table, source_id, lang,
            content, embedding,
            chunk_type, ref_type, ref_id,
            metadata
        )
        VALUES (%s, %s, %s, %s, %s::vector, %s, %s, %s, %s)
        ON CONFLICT (source_table, source_id, lang, chunk_type)
        DO UPDATE SET
            content    = EXCLUDED.content,
            embedding  = EXCLUDED.embedding,
            ref_type   = EXCLUDED.ref_type,
            ref_id     = EXCLUDED.ref_id,
            metadata   = EXCLUDED.metadata,
            updated_at = NOW()
        """,
        (
            "item_i18n",
            source_id,
            lang,
            content,
            embedding_str,
            chunk_type,
            ref_type,
            ref_id,
            json.dumps(metadata, ensure_ascii=False),
        ),
    )


# ── 아이템 처리 (동시 처리용)
async def process_item(
    cursor,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    item_row: dict,
    detail_row: dict | None,
    crafts: list[dict] | None,
):
    item_id = item_row["id"]
    info = parse_jsonb(item_row.get("info")) or {}
    category = item_row.get("category") or ""
    parser = INFO_PARSERS.get(category, parse_default)
    has_spec = bool(parser(info, "en").strip())

    base_metadata = {
        "item_id": item_id,
        "item_name": {
            "ko": get_lang_value(item_row["name"], "ko"),
            "en": get_lang_value(item_row["name"], "en"),
            "ja": get_lang_value(item_row["name"], "ja"),
        },
        "category": category,
        "url": f"https://eftlibrary.com/item/info/{item_row.get('url_mapping') or item_id}",
    }

    docs = [
        {
            "source_id": item_id,
            "chunk_type": "identifier",
            "build_fn": lambda lang, r=item_row: build_identifier_content(r, lang),
            "skip": False,
        },
        {
            "source_id": f"{item_id}_spec",
            "chunk_type": "content",
            "build_fn": lambda lang, r=item_row: build_spec_content(r, lang),
            "skip": not has_spec,
        },
        {
            "source_id": f"{item_id}_detail",
            "chunk_type": "content",
            "build_fn": lambda lang, r=item_row, d=detail_row: build_detail_content(
                r, d, lang
            ),
            "skip": not detail_row,
        },
        {
            "source_id": f"{item_id}_craft",
            "chunk_type": "content",
            "build_fn": lambda lang, r=item_row, c=crafts: build_craft_content(
                r, c or [], lang
            ),
            "skip": not crafts,
        },
    ]

    async with semaphore:
        for doc in docs:
            if doc["skip"]:
                continue

            for lang in LANGS:
                content = doc["build_fn"](lang)

                if not content.strip():
                    log.warning(f"  ⚠ 빈 content 스킵: {doc['source_id']} [{lang}]")
                    continue

                try:
                    embedding = await get_embedding(client, content)
                    upsert_rag_document(
                        cursor,
                        doc["source_id"],
                        lang,
                        content,
                        embedding,
                        doc["chunk_type"],
                        "item",
                        item_id,  # ref_id는 항상 item_id로 통일
                        base_metadata,
                    )
                    log.info(f"  ✓ {doc['source_id']} [{lang}] 완료")

                except httpx.HTTPError as e:
                    log.error(f"  ✗ 임베딩 실패: {doc['source_id']} [{lang}] - {e}")
                except Exception as e:
                    log.error(f"  ✗ DB 저장 실패: {doc['source_id']} [{lang}] - {e}")


# ── 배치 처리
async def _run(postgres_conn_id: str, batch_size: int):
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:

            # 기존 처리된 ID 수집
            existing_ids: set[str] = set()
            if SKIP_EXISTING:
                cursor.execute(
                    "SELECT DISTINCT source_id FROM rag_documents WHERE source_table = 'item_i18n'"
                )
                existing_ids = {row[0] for row in cursor.fetchall()}
                log.info(f"이미 처리된 아이템: {len(existing_ids)}개 스킵")

            cursor.execute("SELECT COUNT(*) FROM item_i18n")
            total = cursor.fetchone()[0]
            log.info(
                f"전체 아이템: {total}개 | 처리 대상: {total - len(existing_ids)}개"
            )

            semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
            offset = 0
            processed = 0

            async with httpx.AsyncClient() as client:
                while offset < total:
                    # 아이템 조회
                    cursor.execute(
                        """
                        SELECT id, name, category, url_mapping, info
                        FROM item_i18n
                        ORDER BY id ASC
                        LIMIT %s OFFSET %s
                        """,
                        (batch_size, offset),
                    )
                    rows = cursor.fetchall()
                    if not rows:
                        break

                    col_names = [desc[0] for desc in cursor.description]
                    item_rows = [dict(zip(col_names, row)) for row in rows]

                    batch_ids = [r["id"] for r in item_rows]
                    target_ids = [id for id in batch_ids if id not in existing_ids]

                    if not target_ids:
                        offset += batch_size
                        continue

                    # detail 조회
                    cursor.execute(
                        """
                        SELECT id, hideout_items, used_in_crafts, rewarded_by_npcs,
                               rewarded_by_quests, required_by_quest_item,
                               rewarded_by_quests_craft_unlock, rewarded_by_quests_offer_unlock
                        FROM item_detail_i18n
                        WHERE id = ANY(%s)
                        """,
                        (target_ids,),
                    )
                    detail_rows = cursor.fetchall()
                    detail_col = [desc[0] for desc in cursor.description]
                    detail_map = {
                        row[0]: dict(zip(detail_col, row)) for row in detail_rows
                    }

                    # craft 조회
                    cursor.execute(
                        """
                        SELECT reward_item_id, level, duration, quantity, req_item, name
                        FROM hideout_crafts_i18n
                        WHERE reward_item_id = ANY(%s)
                        """,
                        (target_ids,),
                    )
                    craft_rows = cursor.fetchall()
                    craft_col = [desc[0] for desc in cursor.description]
                    craft_map: dict[str, list[dict]] = {}
                    for row in craft_rows:
                        rd = dict(zip(craft_col, row))
                        craft_map.setdefault(rd["reward_item_id"], []).append(rd)

                    log.info(
                        f"배치: {offset + 1} ~ {offset + len(item_rows)} / {total} "
                        f"| 대상: {len(target_ids)}개"
                    )

                    tasks = [
                        process_item(
                            cursor,
                            client,
                            semaphore,
                            r,
                            detail_map.get(r["id"]),
                            craft_map.get(r["id"]),
                        )
                        for r in item_rows
                        if r["id"] in target_ids
                    ]
                    await asyncio.gather(*tasks)

                    processed += len(target_ids)
                    offset += batch_size
                    log.info(f"누적 처리: {processed}개")

        conn.commit()
    log.info(f"=== 완료: {processed}개 아이템 처리 ===")


# ── DAG 진입점
def run_item_rag_embed(postgres_conn_id: str = "tkl_db", batch_size: int = BATCH_SIZE):
    asyncio.run(_run(postgres_conn_id, batch_size))
