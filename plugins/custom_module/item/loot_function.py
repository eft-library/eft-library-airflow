import pendulum


def process_loot(item):
    """
    loot 데이터 가공
    """

    id = item.get("id")
    name_en = item.get("name")
    name_kr = get_loot_kr(name_en)
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    category_en = item["category"].get("name") if item.get("category") else None
    category_kr = get_category_kr(category_en)
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name_en,
        name_kr,
        short_name,
        image,
        category_en,
        category_kr,
        update_time,
    )


def get_category_kr(category):
    """
    카테고리 한글
    """

    category_dict = {
        "Others": "기타",
        "Building materials": "건축 자재",
        "Electronics": "전자 제품",
        "Energy elements": "에너지 관련 용품",
        "Flammable materials": "가연성 물질",
        "Household materials": "가정용품",
        "Medical supplies": "의료용품",
        "Tools": "도구",
        "Valuables": "귀중품",
        "Info items": "정보 아이템",
        "Special equipment": "특수 장비",
    }

    if category in category_dict:
        return category_dict[category]
    else:
        return category


def get_loot_kr(name):
    """
    전리품 한글 이름
    """

    return name
