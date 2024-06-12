import pendulum

def process_key(item, key_map):
    """
    key 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    uses = item["properties"].get("uses")
    map_value = get_map_for_key(key_map, name)
    use_map_en = get_use_map_en(map_value)
    use_map_kr = get_use_map_kr(map_value)
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        image,
        uses,
        use_map_en,
        use_map_kr,
        map_value,
        update_time,
    )

def process_key_map(item_list):
    """
    통신으로 가져온 map과 관련된 key 데이터 가공하기
    """
    def get_db_value(name):
        """
        이름을 DB랑 맞추기 위해 사용
        """
        db_value = {
            "Factory": "FACTORY",
            "Customs":"CUSTOM",
            "Woods":"WOODS",
            "Lighthouse":"LIGHT_HOUSE",
            "Shoreline":"SHORELINE",
            "Reserve":"RESERVE",
            "Interchange":"INTERCHANGE",
            "Streets of Tarkov":"STREET_OF_TARKOV",
            "Night Factory":"FACTORY",
            "The Lab":"THE_LAB",
            "Ground Zero":"GROUND_ZERO",
            "Ground Zero 21+":"GROUND_ZERO"
        }
        return db_value[name] if name in db_value else "N/A"

    key_map = {}

    for map_data in item_list:
        map_name = get_db_value(map_data.get("name"))
        for key_data in map_data.get("locks"):
            key_map[key_data.get("key").get("name")] = map_name

    return key_map

def get_map_for_key(key_map, name):
    """
    key_map 객체에서 맵 추출하여 키에 붙이기
    """
    return key_map[name] if name in key_map else "N/A"

def get_use_map_en(map_value):
    """
    사용 맵 영어 이름 가공
    """
    value = {
        "FACTORY": "Factory",
        "CUSTOM":"Custom",
        "WOODS":"Woods",
        "LIGHT_HOUSE":"Lighthouse",
        "SHORELINE":"Shoreline",
        "RESERVE":"Reserve",
        "INTERCHANGE":"Interchange",
        "STREET_OF_TARKOV":"Streets of Tarkov",
        "THE_LAB":"The Lab",
        "GROUND_ZERO":"Ground Zero"
    }
    if map_value in value:
        return value[map_value]
    else:
        return map_value

def get_use_map_kr(map_value):
    """
    사용 맵 한글 이름 가공
    """
    value = {
        "FACTORY": "팩토리",
        "CUSTOM":"세관",
        "WOODS":"삼림",
        "LIGHT_HOUSE":"등대",
        "SHORELINE":"해안선",
        "RESERVE":"리저브",
        "INTERCHANGE":"인터체인지",
        "STREET_OF_TARKOV":"타르코프 시내",
        "THE_LAB":"연구소",
        "GROUND_ZERO":"그라운드 제로"
    }
    if map_value in value:
        return value[map_value]
    else:
        return map_value