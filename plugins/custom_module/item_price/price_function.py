import pendulum
import json


def process_price(item):
    """
    price 데이터 가공
    """
    id = item.get("id")
    item_name_en = item.get("name_en")
    item_image = item.get("image512pxLink")
    trader = json.dumps(item.get("sellFor"))
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        item_name_en,
        item_image,
        trader,
        update_time
    )

def merge_item_price_data(pvp_data, pve_data):
    """
    pvp, pve 데이터 가공
    """
    merged_data = []
    # 두 데이터 리스트를 병합 (ID로 매칭)
    pve_items = {item['id']: item for item in pve_data}

    for pvp_item in pvp_data:
        pve_item = pve_items.get(pvp_item['id'])
        print('pvp', pvp_item)
        print('pve',pve_item)
        # 가격 정보 통합
        merged_item = {
            "id": pvp_item["id"],
            "name_en": pvp_item["name"],
            "image512pxLink": pvp_item["image512pxLink"],
            "sellFor": {
                "pvp_trader": mapping_trader(pvp_item["sellFor"]) if pvp_item["sellFor"] else None,
                "pve_trader": mapping_trader(pve_item["sellFor"]) if pve_item["sellFor"] else None
            },
            # "pvpHistoricalPrices": [{"price_type": "pvp", **price} for price in pvp_item["historicalPrices"]],
            # "pveHistoricalPrices": [{"price_type": "pve", **price} for price in pve_item["historicalPrices"]]
        }

        merged_data.append(merged_item)
        print(merged_item)

    return merged_data


def mapping_trader(sell_for):
    """
    trader 정보 연결
    """
    npc_data = {
        "Peacekeeper": {
            "npc_id": "PEACE_KEEPER",
            "npc_name_en": "Peace Keeper",
            "npc_name_kr": "피스키퍼",
            "npc_image": "/tkl_quest/npc/peacekeeper.webp"
        },
        "Mechanic": {
            "npc_id": "MECHANIC",
            "npc_name_en": "Mechanic",
            "npc_name_kr": "메카닉",
            "npc_image": "/tkl_quest/npc/mechanic.webp"
        },
        "Prapor": {
            "npc_id": "PRAPOR",
            "npc_name_en": "Prapor",
            "npc_name_kr": "프라퍼",
            "npc_image": "/tkl_quest/npc/prapor.webp"
        },
        "Skier": {
            "npc_id": "SKIER",
            "npc_name_en": "Skier",
            "npc_name_kr": "스키어",
            "npc_image": "/tkl_quest/npc/skier.webp"
        },
        "Fence": {
            "npc_id": "FENCE",
            "npc_name_en": "Fence",
            "npc_name_kr": "펜스",
            "npc_image": "/tkl_quest/npc/fence.webp"
        },
        "Therapist": {
            "npc_id": "THERAPIST",
            "npc_name_en": "Therapist",
            "npc_name_kr": "테라피스트",
            "npc_image": "/tkl_quest/npc/therapist.webp"
        },
        "Jaeger": {
            "npc_id": "JAEGER",
            "npc_name_en": "Jaeger",
            "npc_name_kr": "예거",
            "npc_image": "/tkl_quest/npc/jaeger.webp"
        },
        "Ragman": {
            "npc_id": "RAGMAN",
            "npc_name_en": "Ragman",
            "npc_name_kr": "래그맨",
            "npc_image": "/tkl_quest/npc/ragman.webp"
        },
        "Ref": {
            "npc_id": "REF",
            "npc_name_en": "Ref",
            "npc_name_kr": "레프",
            "npc_image": "/tkl_quest/npc/ref.webp"
        },
        "Flea Market": {
            "npc_id": "FLEA_MARKET",
            "npc_name_en": "Flea Market",
            "npc_name_kr": "플리마켓",
            "npc_image": "/tkl_quest/npc/ragman.webp"
        },
    }

    process_sell = []
    for sell in sell_for:
        new_sell = {
            'price': sell.get('priceRUB'),
            'trader': npc_data.get(sell['vendor']['name'])
        }
        process_sell.append(new_sell)

    return process_sell