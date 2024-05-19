import requests


def read_sql(sql_path):
    with open('/home/airflow/plugins/sql/' + sql_path, 'r') as file:
        sql_query = file.read()
        return sql_query


def get_weapon():
    query = """
    {
         items {
            id
            name
            shortName
            image512pxLink
            category {
              name
              parent {
                name
              }
            }
            properties {
              ... on ItemPropertiesWeapon {
                caliber
                defaultAmmo {
                  name
                }
                fireModes
                fireRate
                defaultErgonomics
                defaultRecoilVertical
                defaultRecoilHorizontal
            }
          }
        }
    }
    """
    headers = {"Content-Type": "application/json"}
    response = requests.post('https://api.tarkov.dev/graphql', headers=headers, json={'query': query})
    if response.status_code == 200:
        # 데이터 변환
        filtered_items = [
            item for item in response.json()['data']['items']
            if item['category']['parent']['name'] == "Weapon" and item['properties'] != {}
        ]
        return filtered_items
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(response.status_code, query))

def weapon_data_check(item):
    import pendulum

    weapon_id = item.get('id')
    weapon_name = item.get('name')
    weapon_short_name = item.get('shortName')
    weapon_img = item.get('image512pxLink')
    weapon_category = item['category'].get('name') if item.get('category') else None
    weapon_carliber = item['properties'].get('caliber') if item.get('properties') else None
    weapon_default_ammo = item['properties']['defaultAmmo'].get('name') if item.get('properties') and item[
        'properties'].get('defaultAmmo') else None
    weapon_modes_en = item['properties'].get('fireModes') if item.get('properties') else None
    weapon_fire_rate = item['properties'].get('fireRate') if item.get('properties') else None
    weapon_ergonomics = item['properties'].get('defaultErgonomics') if item.get('properties') else None
    weapon_recoil_vertical = item['properties'].get('defaultRecoilVertical') if item.get(
        'properties') else None
    weapon_recoil_horizontal = item['properties'].get('defaultRecoilHorizontal') if item.get(
        'properties') else None
    weapon_update_time = pendulum.now('Asia/Seoul')

    weapon_modes_kr = []
    for mode in weapon_modes_en:
        if 'Single fire' in mode:
            weapon_modes_kr.append("단발")
        if 'Full auto' in mode:
            weapon_modes_kr.append("자동")
        if 'Burst Fire' in mode:
            weapon_modes_kr.append("점사")
        if 'Double-Tap' in mode:
            weapon_modes_kr.append("더블 탭")
        if 'Double action' in mode:
            weapon_modes_kr.append("더블 액션")
        if 'Semi-auto' in mode:
            weapon_modes_kr.append("반자동")

    values = (
        weapon_id,
        weapon_name,
        weapon_short_name,
        weapon_img,
        weapon_category,
        weapon_carliber,
        weapon_default_ammo,
        weapon_modes_en,
        weapon_modes_kr,
        weapon_fire_rate,
        weapon_ergonomics,
        weapon_recoil_vertical,
        weapon_recoil_horizontal,
        weapon_update_time,
        weapon_id
    )

    return values