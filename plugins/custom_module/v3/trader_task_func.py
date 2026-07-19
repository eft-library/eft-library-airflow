import hashlib
import json
import re
from decimal import Decimal, InvalidOperation


def generate_trader_graphql(lang: str) -> str:
    return f"""
{{
  traders(lang: {lang}) {{
    id
    name
    imageLink
    barters {{
      level
      requiredItems {{
        item {{
          id
        }}
        quantity
      }}
      rewardItems {{
        item {{
          id
        }}
        quantity
      }}
    }}
  }}
}}
"""


def v3_trader_process(item_en, item_ko, item_ja):
    item_ko = item_ko or {}
    item_ja = item_ja or {}
    trader_id = item_en.get("id")
    name_en = item_en.get("name")
    name_ko = item_ko.get("name")
    name_ja = item_ja.get("name")
    image = item_en.get("imageLink")
    normalized_name = normalize_trader_name(name_en)

    return (trader_id, name_en, name_ko, name_ja, image, normalized_name)


def normalize_trader_name(name_en):
    if not name_en:
        return None

    normalized_name = name_en.lower()
    normalized_name = re.sub(r"['\"]", "", normalized_name)
    normalized_name = re.sub(r"[^a-z0-9]+", "-", normalized_name)
    normalized_name = re.sub(r"-+", "-", normalized_name).strip("-")

    return normalized_name or None


def v3_trader_barter_process(trader_en):
    barter_rows = []
    required_rows = []
    reward_rows = []

    trader_id = trader_en.get("id")
    barters = trader_en.get("barters", [])

    if not trader_id:
        return barter_rows, required_rows, reward_rows

    def item_signature(item_info):
        quantity = item_info.get("quantity", 0)
        try:
            quantity = format(Decimal(str(quantity)).normalize(), "f")
        except (InvalidOperation, TypeError, ValueError):
            quantity = str(quantity)
        return (
            (item_info.get("item") or {}).get("id") or "",
            quantity,
        )

    def barter_signature(barter):
        payload = {
            "level": barter.get("level"),
            "required": sorted(
                item_signature(item) for item in barter.get("requiredItems", [])
            ),
            "reward": sorted(
                item_signature(item) for item in barter.get("rewardItems", [])
            ),
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    sorted_barters = sorted(
        ((barter_signature(barter), barter) for barter in barters),
        key=lambda value: value[0],
    )
    signature_counts = {}

    for signature, barter in sorted_barters:
        trader_level = barter.get("level")
        if trader_level is None:
            continue

        occurrence = signature_counts.get(signature, 0)
        signature_counts[signature] = occurrence + 1
        barter_id = f"{trader_id}-barter-{signature}-{occurrence}"

        barter_rows.append(
            (
                barter_id,
                trader_id,
                trader_level,
            )
        )

        required_items = sorted(
            barter.get("requiredItems", []), key=item_signature
        )
        for req_idx, req in enumerate(required_items):
            item_id = req.get("item", {}).get("id")
            quantity = req.get("quantity", 0)

            if not item_id:
                continue

            required_id = f"{barter_id}-req-{req_idx}"

            required_rows.append(
                (
                    required_id,
                    barter_id,
                    item_id,
                    quantity,
                )
            )

        reward_items = sorted(
            barter.get("rewardItems", []), key=item_signature
        )
        for reward_idx, reward in enumerate(reward_items):
            item_id = reward.get("item", {}).get("id")
            quantity = reward.get("quantity", 0)

            if not item_id:
                continue

            reward_id = f"{barter_id}-reward-{reward_idx}"

            reward_rows.append(
                (
                    reward_id,
                    barter_id,
                    item_id,
                    quantity,
                )
            )

    return barter_rows, required_rows, reward_rows
