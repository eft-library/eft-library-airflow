import json
import pendulum


def process_provisions(item):
    """
    provisions 데이터 가공
    """
    id = item.get("id")
    name_en = item.get("name")
    name_kr = provisions_kr(name_en)
    short_name = item.get("shortName")
    category = item["category"].get("name") if item.get("category") else None
    energy = item["properties"].get("energy") if item.get("properties") else None
    hydration = item["properties"].get("hydration") if item.get("properties") else None
    stim_effects = (
        item["properties"].get("stimEffects") if item.get("properties") else None
    )
    new_stim_effects = process_stim_effect(stim_effects)
    result_stim_effects = json.dumps(add_painkiller(new_stim_effects, name_en))
    image = item.get("image512pxLink")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name_en,
        name_kr,
        short_name,
        category,
        energy,
        hydration,
        result_stim_effects,
        image,
        update_time,
    )


def provisions_kr(name):
    """
    한글 이름 매핑
    """
    provision_kr = {
        "Bottle of water (0.6L)": "Water 0.6L 물병",
        "Army crackers": "Crackers 군용 크래커",
        "Pack of Russian Army pineapple juice": "Pineapple 러시아군 파인애플 주스",
        "Slickers chocolate bar": "Slickers 슬리커스 초콜릿 바",
        "Can of pacific saury": "Pacific saury 꽁치 통조림",
        "Can of condensed milk": "Condensed milk 연유",
        "Rye croutons": "Rye croutons 호밀 크루통",
        "Can of humpback salmon": "Humpback 곱사연어 통조림",
        "Can of green peas": "Green peas 녹색 완두콩 통조림",
        "Can of beef stew (Small)": "Beef stew (small) 투숀카 (소형)",
        "Can of squash spread": "Squash 호박 스프레드 통조림",
        "Pack of oat flakes": "Oat flakes 귀리 플레이크 팩",
        "Can of herring": "Herring 청어 통조림",
        "Can of beef stew (Large)": "Beef stew (large) 투숀카 (대형)",
        "Alyonka chocolate bar": "Alyonka 알룐카 초콜릿 바",
        "Can of Ice Green tea": "Ice Green tea 아이스 녹차 캔",
        "Pack of apple juice": "Apple 사과주스",
        "Pack of Grand juice": "Grand 그랜드 자몽 주스",
        "Pack of Vita juice": "Vita 비타 주스",
        "Can of Max Energy energy drink": "Max Energy 맥스 에너지",
        "Can of TarCola soda": "TarCola 타르콜라",
        "Pack of milk": "Milk 우유 팩",
        "Emelya rye croutons": "Emelya 에멜야 호밀 크루통",
        "Can of Hot Rod energy drink": "Hot Rod 핫 로드 에너지 드링크",
        "Iskra ration pack": "Iskra 전투식량",
        "MRE ration pack": "MRE 전투식량",
        "Pack of sugar": "Sugar 설탕 팩",
        "Jar of DevilDog mayo": "DevilDog 마요네즈 병",
        "Can of sprats": "Sprats 스프랫 통조림",
        "Aquamari water bottle with filter": "Aquamari 아쿠아마리 필터 달린 물병",
        "Canister with purified water": "Purified water 정제수",
        "Bottle of Fierce Hatchling moonshine": "Moonshine 문샤인 '맹렬한 도끼런' 밀주",
        "Bottle of Dan Jackiel whiskey": "Whiskey 댄 잭키엘 위스키",
        "Bottle of Tarkovskaya vodka": "Vodka 타르코프스카야 보드카",
        'Bottle of "Norvinskiy Yadreniy" premium kvass (0.6L)': "Kvass 프리미엄 크바스 '노르빈스키 야드레니' 0.6L",
        "Emergency Water Ration": "EWR 비상용 식수",
        "Can of RatCola soda": "Rat Cola 탄산음료",
        "Bottle of Pevko Light beer": "Pevko Light 병맥주",
        "Salty Dog beef sausage": "Salty Dog beef sausage",
        "Pack of instant noodles": "Pack of instant noodles",
        "Pack of Tarker dried meat": "Pack of Tarker dried meat",
    }

    if name in provision_kr:
        return provision_kr[name]
    return name


def process_stim_effect(stim_effects):
    """
    stim effect 효과 추가
    """
    new_effects = stim_effects
    kr_skill = {
        "Intellect": "지력",
        "Attention": "주의력",
        "Stress Resistance": "스트레스 저항력",
        "Endurance": "지구력",
        "Mag Drills": "탄창 훈련",
        "Strength": "근력",
        "Metabolism": "신진대사",
        "Memory": "기억력",
        "Health": "체력",
        "Vitality": "활력",
        "Immunity": "면역력",
        "Perception": "인지능력",
        "Charisma": "카리스마",
    }

    kr_type = {
        "Energy recovery": "에너지 회복",
        "Health regeneration": "체력 재생",
        "Hands tremor": "손 떨림",
        "Hydration recovery": "수분 회복",
    }

    for effects in new_effects:
        if effects["type"] == "Skill" and effects["skillName"] in kr_skill:
            effects["krSkill"] = kr_skill[effects["skillName"]]
        else:
            if effects["type"] in kr_type:
                effects["krSkill"] = kr_type[effects["type"]]

    return new_effects


def add_painkiller(stim_effects, name):
    """
    진통제 추가
    """
    new_effects = stim_effects

    painkiller = {
        "Bottle of Dan Jackiel whiskey": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "krSkill": "진통제",
            "duration": 210,
            "skillName": "Painkiller",
        },
        "Bottle of Tarkovskaya vodka": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "krSkill": "진통제",
            "duration": 250,
            "skillName": "Painkiller",
        },
        "Bottle of Fierce Hatchling moonshine": {
            "type": "Skill",
            "delay": 1,
            "value": 1,
            "krSkill": "진통제",
            "duration": 500,
            "skillName": "Painkiller",
        },
    }

    if name in painkiller:
        new_effects.append(painkiller[name])

    return new_effects
