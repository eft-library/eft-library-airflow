import pendulum


def process_ammo(item):
    """
    ammo 데이터 가공
    """
    id = item.get("id")
    name = item.get("name")
    short_name = item.get("shortName")
    category = get_category(name)
    round = get_round(name)
    damage = item["properties"].get("damage") if item.get("properties") else None
    penetration_power = (
        item["properties"].get("penetrationPower") if item.get("properties") else None
    )
    armor_damage = (
        item["properties"].get("armorDamage") if item.get("properties") else None
    )
    accuracy_modifier = (
        item["properties"].get("accuracyModifier") if item.get("properties") else None
    )
    recoil_modifier = (
        item["properties"].get("recoilModifier") if item.get("properties") else None
    )
    light_bleed_modifier = (
        item["properties"].get("lightBleedModifier") if item.get("properties") else None
    )
    heavy_bleed_modifier = (
        item["properties"].get("heavyBleedModifier") if item.get("properties") else None
    )
    efficiency = get_efficiency(name)
    image = item.get("image512pxLink")
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name,
        short_name,
        category,
        round,
        damage,
        penetration_power,
        armor_damage,
        accuracy_modifier,
        recoil_modifier,
        light_bleed_modifier,
        heavy_bleed_modifier,
        efficiency,
        image,
        update_time,
    )


def get_round(name):
    """
    round 정의
    """
    round_dict = {
        "7.62x25mm TT LRNPC": "Pistol Rounds",
        "7.62x25mm TT LRN": "Pistol Rounds",
        "7.62x25mm TT FMJ43": "Pistol Rounds",
        "7.62x25mm TT AKBS": "Pistol Rounds",
        "7.62x25mm TT P gl": "Pistol Rounds",
        "7.62x25mm TT PT gzh": "Pistol Rounds",
        "7.62x25mm TT Pst gzh": "Pistol Rounds",
        "9x18mm PM SP8 gzh": "Pistol Rounds",
        "9x18mm PM SP7 gzh": "Pistol Rounds",
        "9x18mm PM PSV": "Pistol Rounds",
        "9x18mm PM P gzh": "Pistol Rounds",
        "9x18mm PM PSO gzh": "Pistol Rounds",
        "9x18mm PM PS gs PPO": "Pistol Rounds",
        "9x18mm PM PRS gs": "Pistol Rounds",
        "9x18mm PM PPe gzh": "Pistol Rounds",
        "9x18mm PM PPT gzh": "Pistol Rounds",
        "9x18mm PM Pst gzh": "Pistol Rounds",
        "9x18mm PM RG028 gzh": "Pistol Rounds",
        "9x18mm PM BZhT gzh": "Pistol Rounds",
        "9x18mm PMM PstM gzh": "Pistol Rounds",
        "9x18mm PM PBM gzh": "Pistol Rounds",
        "9x19mm RIP": "Pistol Rounds",
        "9x19mm QuakeMaker": "Pistol Rounds",
        "9x19mm PSO gzh": "Pistol Rounds",
        "9x19mm Luger CCI": "Pistol Rounds",
        "9x19mm Green Tracer": "Pistol Rounds",
        "9x19mm FMJ M882": "Pistol Rounds",
        "9x19mm Pst gzh": "Pistol Rounds",
        "9x19mm AP 6.3": "Pistol Rounds",
        "9x19mm PBP gzh": "Pistol Rounds",
        "9x21mm PE gzh": "Pistol Rounds",
        "9x21mm P gzh": "Pistol Rounds",
        "9x21mm PS gzh": "Pistol Rounds",
        "9x21mm 7U4": "Pistol Rounds",
        "9x21mm BT gzh": "Pistol Rounds",
        '9x21mm 7N42 "Zubilo"': "Pistol Rounds",
        ".357 Magnum SP": "Pistol Rounds",
        ".357 Magnum HP": "Pistol Rounds",
        ".357 Magnum JHP": "Pistol Rounds",
        ".357 Magnum FMJ": "Pistol Rounds",
        ".45 ACP RIP": "Pistol Rounds",
        ".45 ACP Hydra-Shok": "Pistol Rounds",
        ".45 ACP Lasermatch FMJ": "Pistol Rounds",
        ".45 ACP Match FMJ": "Pistol Rounds",
        ".45 ACP AP": "Pistol Rounds",
        "4.6x30mm Action SX": "PDW Rounds",
        "4.6x30mm Subsonic SX": "PDW Rounds",
        "4.6x30mm JSP SX": "PDW Rounds",
        "4.6x30mm FMJ SX": "PDW Rounds",
        "4.6x30mm AP SX": "PDW Rounds",
        "5.7x28mm R37.F": "PDW Rounds",
        "5.7x28mm R37.X": "PDW Rounds",
        "5.7x28mm SS198LF": "PDW Rounds",
        "5.7x28mm SS197SR": "PDW Rounds",
        "5.7x28mm SB193": "PDW Rounds",
        "5.7x28mm L191": "PDW Rounds",
        "5.7x28mm SS190": "PDW Rounds",
        "5.45x39mm HP": "Rifle Rounds",
        "5.45x39mm PRS gs": "Rifle Rounds",
        "5.45x39mm SP": "Rifle Rounds",
        "5.45x39mm US gs": "Rifle Rounds",
        "5.45x39mm T gs": "Rifle Rounds",
        "5.45x39mm FMJ": "Rifle Rounds",
        "5.45x39mm PS gs": "Rifle Rounds",
        "5.45x39mm PP gs": "Rifle Rounds",
        "5.45x39mm BT gs": "Rifle Rounds",
        "5.45x39mm 7N40": "Rifle Rounds",
        "5.45x39mm BP gs": "Rifle Rounds",
        "5.45x39mm BS gs": "Rifle Rounds",
        '5.45x39mm PPBS gs "Igolnik"': "Rifle Rounds",
        "5.56x45mm Warmageddon": "Rifle Rounds",
        "5.56x45mm HP": "Rifle Rounds",
        "5.56x45mm MK 255 Mod 0 (RRLP)": "Rifle Rounds",
        "5.56x45mm M856": "Rifle Rounds",
        "5.56x45mm FMJ": "Rifle Rounds",
        "5.56x45mm M855": "Rifle Rounds",
        "5.56x45mm MK 318 Mod 0 (SOST)": "Rifle Rounds",
        "5.56x45mm M856A1": "Rifle Rounds",
        "5.56x45mm M855A1": "Rifle Rounds",
        "5.56x45mm M995": "Rifle Rounds",
        "5.56x45mm SSA AP": "Rifle Rounds",
        "6.8x51mm SIG FMJ": "Rifle Rounds",
        "6.8x51mm SIG Hybrid": "Rifle Rounds",
        ".300 Whisper": "Rifle Rounds",
        ".300 Blackout V-Max": "Rifle Rounds",
        ".300 Blackout BCP FMJ": "Rifle Rounds",
        ".300 Blackout M62 Tracer": "Rifle Rounds",
        ".300 Blackout CBJ": "Rifle Rounds",
        ".300 Blackout AP": "Rifle Rounds",
        "7.62x39mm HP": "Rifle Rounds",
        "7.62x39mm SP": "Rifle Rounds",
        "7.62x39mm FMJ": "Rifle Rounds",
        "7.62x39mm US gzh": "Rifle Rounds",
        "7.62x39mm T-45M1 gzh": "Rifle Rounds",
        "7.62x39mm PS gzh": "Rifle Rounds",
        "7.62x39mm PP gzh": "Rifle Rounds",
        "7.62x39mm BP gzh": "Rifle Rounds",
        "7.62x39mm MAI AP": "Rifle Rounds",
        "7.62x51mm Ultra Nosler": "Rifle Rounds",
        "7.62x51mm TCW SP": "Rifle Rounds",
        "7.62x51mm BCP FMJ": "Rifle Rounds",
        "7.62x51mm M80": "Rifle Rounds",
        "7.62x51mm M62 Tracer": "Rifle Rounds",
        "7.62x51mm M61": "Rifle Rounds",
        "7.62x51mm M993": "Rifle Rounds",
        "7.62x54mm R HP BT": "Rifle Rounds",
        "7.62x54mm R SP BT": "Rifle Rounds",
        "7.62x54mm R FMJ": "Rifle Rounds",
        "7.62x54mm R T-46M gzh": "Rifle Rounds",
        "7.62x54mm R LPS gzh": "Rifle Rounds",
        "7.62x54mm R PS gzh": "Rifle Rounds",
        "7.62x54mm R BT gzh": "Rifle Rounds",
        "7.62x54mm R SNB gzh": "Rifle Rounds",
        "7.62x54mm R BS gs": "Rifle Rounds",
        ".338 Lapua Magnum TAC-X": "Rifle Rounds",
        ".338 Lapua Magnum UCW": "Rifle Rounds",
        ".338 Lapua Magnum FMJ": "Rifle Rounds",
        ".338 Lapua Magnum AP": "Rifle Rounds",
        "9x39mm FMJ": "Rifle Rounds",
        "9x39mm SP-5 gs": "Rifle Rounds",
        "9x39mm SPP gs": "Rifle Rounds",
        "9x39mm PAB-9 gs": "Rifle Rounds",
        "9x39mm SP-6 gs": "Rifle Rounds",
        "9x39mm BP gs": "Rifle Rounds",
        ".366 TKM Geksa": "Rifle Rounds",
        ".366 TKM FMJ": "Rifle Rounds",
        ".366 TKM EKO": "Rifle Rounds",
        ".366 TKM AP-M": "Rifle Rounds",
        "12.7x55mm PS12A": "Rifle Rounds",
        "12.7x55mm PS12": "Rifle Rounds",
        "12.7x55mm PS12B": "Rifle Rounds",
        "12/70 5.25mm buckshot": "Shotgun Rounds",
        "12/70 8.5mm Magnum buckshot": "Shotgun Rounds",
        "12/70 6.5mm Express buckshot": "Shotgun Rounds",
        "12/70 7mm buckshot": "Shotgun Rounds",
        "12/70 Piranha": "Shotgun Rounds",
        "12/70 flechette": "Shotgun Rounds",
        "12/70 RIP": "Shotgun Rounds",
        "12/70 SuperFormance HP slug": "Shotgun Rounds",
        "12/70 Grizzly 40 slug": "Shotgun Rounds",
        "12/70 Copper Sabot Premier HP slug": "Shotgun Rounds",
        "12/70 lead slug": "Shotgun Rounds",
        '12/70 "Poleva-3" slug': "Shotgun Rounds",
        "12/70 Dual Sabot slug": "Shotgun Rounds",
        "12/70 FTX Custom Lite slug": "Shotgun Rounds",
        '12/70 "Poleva-6u" slug': "Shotgun Rounds",
        "12/70 makeshift .50 BMG slug": "Shotgun Rounds",
        "12/70 AP-20 armor-piercing slug": "Shotgun Rounds",
        "20/70 5.6mm buckshot": "Shotgun Rounds",
        "20/70 6.2mm buckshot": "Shotgun Rounds",
        "20/70 7.5mm buckshot": "Shotgun Rounds",
        "20/70 7.3mm buckshot": "Shotgun Rounds",
        "20/70 Devastator slug": "Shotgun Rounds",
        '20/70 "Poleva-3" slug': "Shotgun Rounds",
        "20/70 Star slug": "Shotgun Rounds",
        '20/70 "Poleva-6u" slug': "Shotgun Rounds",
        "23x75mm Zvezda flashbang round": "Shotgun Rounds",
        "23x75mm Shrapnel-25 buckshot": "Shotgun Rounds",
        "23x75mm Shrapnel-10 buckshot": "Shotgun Rounds",
        "23x75mm Barrikada slug": "Shotgun Rounds",
        "40x46mm M576 (MP-APERS) grenade": "Other",
        "30x29mm VOG-30 E": "Other",
        "12.7x108mm BZT-44M": "Other",
        "12.7x108mm B-32 T": "Other",
    }

    if name in round_dict:
        return round_dict[name]
    return ""


def get_category(name):
    """
    category 정의
    """

    category = {
        "7.62x25mm TT LRNPC": "7.62x25mm Tokarev",
        "7.62x25mm TT LRN": "7.62x25mm Tokarev",
        "7.62x25mm TT FMJ43": "7.62x25mm Tokarev",
        "7.62x25mm TT AKBS": "7.62x25mm Tokarev",
        "7.62x25mm TT P gl": "7.62x25mm Tokarev",
        "7.62x25mm TT PT gzh": "7.62x25mm Tokarev",
        "7.62x25mm TT Pst gzh": "7.62x25mm Tokarev",
        "9x18mm PM SP8 gzh": "9x18mm Makarov",
        "9x18mm PM SP7 gzh": "9x18mm Makarov",
        "9x18mm PM PSV": "9x18mm Makarov",
        "9x18mm PM P gzh": "9x18mm Makarov",
        "9x18mm PM PSO gzh": "9x18mm Makarov",
        "9x18mm PM PS gs PPO": "9x18mm Makarov",
        "9x18mm PM PRS gs": "9x18mm Makarov",
        "9x18mm PM PPe gzh": "9x18mm Makarov",
        "9x18mm PM PPT gzh": "9x18mm Makarov",
        "9x18mm PM Pst gzh": "9x18mm Makarov",
        "9x18mm PM RG028 gzh": "9x18mm Makarov",
        "9x18mm PM BZhT gzh": "9x18mm Makarov",
        "9x18mm PMM PstM gzh": "9x18mm Makarov",
        "9x18mm PM PBM gzh": "9x18mm Makarov",
        "9x19mm RIP": "9x19mm Parabellum",
        "9x19mm QuakeMaker": "9x19mm Parabellum",
        "9x19mm PSO gzh": "9x19mm Parabellum",
        "9x19mm Luger CCI": "9x19mm Parabellum",
        "9x19mm Green Tracer": "9x19mm Parabellum",
        "9x19mm FMJ M882": "9x19mm Parabellum",
        "9x19mm Pst gzh": "9x19mm Parabellum",
        "9x19mm AP 6.3": "9x19mm Parabellum",
        "9x19mm PBP gzh": "9x19mm Parabellum",
        "9x21mm PE gzh": "9x21mm Gyurza",
        "9x21mm P gzh": "9x21mm Gyurza",
        "9x21mm PS gzh": "9x21mm Gyurza",
        "9x21mm 7U4": "9x21mm Gyurza",
        "9x21mm BT gzh": "9x21mm Gyurza",
        '9x21mm 7N42 "Zubilo"': "9x21mm Gyurza",
        ".357 Magnum SP": ".357 Magnum",
        ".357 Magnum HP": ".357 Magnum",
        ".357 Magnum JHP": ".357 Magnum",
        ".357 Magnum FMJ": ".357 Magnum",
        ".45 ACP RIP": ".45 ACP",
        ".45 ACP Hydra-Shok": ".45 ACP",
        ".45 ACP Lasermatch FMJ": ".45 ACP",
        ".45 ACP Match FMJ": ".45 ACP",
        ".45 ACP AP": ".45 ACP",
        "4.6x30mm Action SX": "4.6x30mm HK",
        "4.6x30mm Subsonic SX": "4.6x30mm HK",
        "4.6x30mm JSP SX": "4.6x30mm HK",
        "4.6x30mm FMJ SX": "4.6x30mm HK",
        "4.6x30mm AP SX": "4.6x30mm HK",
        "5.7x28mm R37.F": "5.7x28mm FN",
        "5.7x28mm R37.X": "5.7x28mm FN",
        "5.7x28mm SS198LF": "5.7x28mm FN",
        "5.7x28mm SS197SR": "5.7x28mm FN",
        "5.7x28mm SB193": "5.7x28mm FN",
        "5.7x28mm L191": "5.7x28mm FN",
        "5.7x28mm SS190": "5.7x28mm FN",
        "5.45x39mm HP": "5.45x39mm",
        "5.45x39mm PRS gs": "5.45x39mm",
        "5.45x39mm SP": "5.45x39mm",
        "5.45x39mm US gs": "5.45x39mm",
        "5.45x39mm T gs": "5.45x39mm",
        "5.45x39mm FMJ": "5.45x39mm",
        "5.45x39mm PS gs": "5.45x39mm",
        "5.45x39mm PP gs": "5.45x39mm",
        "5.45x39mm BT gs": "5.45x39mm",
        "5.45x39mm 7N40": "5.45x39mm",
        "5.45x39mm BP gs": "5.45x39mm",
        "5.45x39mm BS gs": "5.45x39mm",
        '5.45x39mm PPBS gs "Igolnik"': "5.45x39mm",
        "5.56x45mm Warmageddon": "5.56x45mm NATO",
        "5.56x45mm HP": "5.56x45mm NATO",
        "5.56x45mm MK 255 Mod 0 (RRLP)": "5.56x45mm NATO",
        "5.56x45mm M856": "5.56x45mm NATO",
        "5.56x45mm FMJ": "5.56x45mm NATO",
        "5.56x45mm M855": "5.56x45mm NATO",
        "5.56x45mm MK 318 Mod 0 (SOST)": "5.56x45mm NATO",
        "5.56x45mm M856A1": "5.56x45mm NATO",
        "5.56x45mm M855A1": "5.56x45mm NATO",
        "5.56x45mm M995": "5.56x45mm NATO",
        "5.56x45mm SSA AP": "5.56x45mm NATO",
        "6.8x51mm SIG FMJ": "6.8x51mm",
        "6.8x51mm SIG Hybrid": "6.8x51mm",
        ".300 Whisper": ".300 Blackout",
        ".300 Blackout V-Max": ".300 Blackout",
        ".300 Blackout BCP FMJ": ".300 Blackout",
        ".300 Blackout M62 Tracer": ".300 Blackout",
        ".300 Blackout CBJ": ".300 Blackout",
        ".300 Blackout AP": ".300 Blackout",
        "7.62x39mm HP": "7.62x39mm",
        "7.62x39mm SP": "7.62x39mm",
        "7.62x39mm FMJ": "7.62x39mm",
        "7.62x39mm US gzh": "7.62x39mm",
        "7.62x39mm T-45M1 gzh": "7.62x39mm",
        "7.62x39mm PS gzh": "7.62x39mm",
        "7.62x39mm PP gzh": "7.62x39mm",
        "7.62x39mm BP gzh": "7.62x39mm",
        "7.62x39mm MAI AP": "7.62x39mm",
        "7.62x51mm Ultra Nosler": "7.62x51mm NATO",
        "7.62x51mm TCW SP": "7.62x51mm NATO",
        "7.62x51mm BCP FMJ": "7.62x51mm NATO",
        "7.62x51mm M80": "7.62x51mm NATO",
        "7.62x51mm M62 Tracer": "7.62x51mm NATO",
        "7.62x51mm M61": "7.62x51mm NATO",
        "7.62x51mm M993": "7.62x51mm NATO",
        "7.62x54mm R HP BT": "7.62x54mmR",
        "7.62x54mm R SP BT": "7.62x54mmR",
        "7.62x54mm R FMJ": "7.62x54mmR",
        "7.62x54mm R T-46M gzh": "7.62x54mmR",
        "7.62x54mm R LPS gzh": "7.62x54mmR",
        "7.62x54mm R PS gzh": "7.62x54mmR",
        "7.62x54mm R BT gzh": "7.62x54mmR",
        "7.62x54mm R SNB gzh": "7.62x54mmR",
        "7.62x54mm R BS gs": "7.62x54mmR",
        ".338 Lapua Magnum TAC-X": ".338 Lapua Magnum",
        ".338 Lapua Magnum UCW": ".338 Lapua Magnum",
        ".338 Lapua Magnum FMJ": ".338 Lapua Magnum",
        ".338 Lapua Magnum AP": ".338 Lapua Magnum",
        "9x39mm FMJ": "9x39mm",
        "9x39mm SP-5 gs": "9x39mm",
        "9x39mm SPP gs": "9x39mm",
        "9x39mm PAB-9 gs": "9x39mm",
        "9x39mm SP-6 gs": "9x39mm",
        "9x39mm BP gs": "9x39mm",
        ".366 TKM Geksa": ".366 TKM",
        ".366 TKM FMJ": ".366 TKM",
        ".366 TKM EKO": ".366 TKM",
        ".366 TKM AP-M": ".366 TKM",
        "12.7x55mm PS12A": "12.7x55mm STs-130",
        "12.7x55mm PS12": "12.7x55mm STs-131",
        "12.7x55mm PS12B": "12.7x55mm STs-132",
        "12/70 5.25mm buckshot": "12/70",
        "12/70 8.5mm Magnum buckshot": "12/71",
        "12/70 6.5mm Express buckshot": "12/72",
        "12/70 7mm buckshot": "12/73",
        "12/70 Piranha": "12/74",
        "12/70 flechette": "12/75",
        "12/70 RIP": "12/76",
        "12/70 SuperFormance HP slug": "12/77",
        "12/70 Grizzly 40 slug": "12/78",
        "12/70 Copper Sabot Premier HP slug": "12/79",
        "12/70 lead slug": "12/80",
        '12/70 "Poleva-3" slug': "12/81",
        "12/70 Dual Sabot slug": "12/82",
        "12/70 FTX Custom Lite slug": "12/83",
        '12/70 "Poleva-6u" slug': "12/84",
        "12/70 makeshift .50 BMG slug": "12/85",
        "12/70 AP-20 armor-piercing slug": "12/86",
        "20/70 5.6mm buckshot": "20/70",
        "20/70 6.2mm buckshot": "20/71",
        "20/70 7.5mm buckshot": "20/72",
        "20/70 7.3mm buckshot": "20/73",
        "20/70 Devastator slug": "20/74",
        '20/70 "Poleva-3" slug': "20/75",
        "20/70 Star slug": "20/76",
        '20/70 "Poleva-6u" slug': "20/77",
        "23x75mm Zvezda flashbang round": "23x75mm",
        "23x75mm Shrapnel-25 buckshot": "23x75mm",
        "23x75mm Shrapnel-10 buckshot": "23x75mm",
        "23x75mm Barrikada slug": "23x75mm",
        "40x46mm M576 (MP-APERS) grenade": "40x46mm",
        "30x29mm VOG-30 E": "Stationary weapons",
        "12.7x108mm BZT-44M": "Stationary weapons",
        "12.7x108mm B-32 T": "Stationary weapons",
    }

    if name in category:
        return category[name]
    return ""


def get_efficiency(name):
    """
    efficiency 정의
    """

    efficiency = {
        "7.62x25mm TT LRNPC": [5, 0, 0, 0, 0, 0],
        "7.62x25mm TT LRN": [5, 0, 0, 0, 0, 0],
        "7.62x25mm TT FMJ43": [6, 1, 0, 0, 0, 0],
        "7.62x25mm TT AKBS": [6, 2, 0, 0, 0, 0],
        "7.62x25mm TT P gl": [6, 3, 0, 0, 0, 0],
        "7.62x25mm TT PT gzh": [6, 4, 0, 0, 0, 0],
        "7.62x25mm TT Pst gzh": [6, 6, 4, 1, 0, 0],
        "9x18mm PM SP8 gzh": [0, 0, 0, 0, 0, 0],
        "9x18mm PM SP7 gzh": [0, 0, 0, 0, 0, 0],
        "9x18mm PM PSV": [0, 0, 0, 0, 0, 0],
        "9x18mm PM P gzh": [2, 0, 0, 0, 0, 0],
        "9x18mm PM PSO gzh": [2, 0, 0, 0, 0, 0],
        "9x18mm PM PS gs PPO": [3, 0, 0, 0, 0, 0],
        "9x18mm PM PRS gs": [3, 0, 0, 0, 0, 0],
        "9x18mm PM PPe gzh": [4, 0, 0, 0, 0, 0],
        "9x18mm PM PPT gzh": [5, 1, 0, 0, 0, 0],
        "9x18mm PM Pst gzh": [6, 1, 0, 0, 0, 0],
        "9x18mm PM RG028 gzh": [6, 2, 0, 0, 0, 0],
        "9x18mm PM BZhT gzh": [6, 5, 1, 0, 0, 0],
        "9x18mm PMM PstM gzh": [6, 6, 4, 0, 0, 0],
        "9x18mm PM PBM gzh": [6, 6, 5, 1, 0, 0],
        "9x19mm RIP": [0, 0, 0, 0, 0, 0],
        "9x19mm QuakeMaker": [6, 1, 0, 0, 0, 0],
        "9x19mm PSO gzh": [6, 2, 0, 0, 0, 0],
        "9x19mm Luger CCI": [6, 2, 0, 0, 0, 0],
        "9x19mm Green Tracer": [6, 3, 1, 0, 0, 0],
        "9x19mm FMJ M882": [6, 5, 2, 0, 0, 0],
        "9x19mm Pst gzh": [6, 6, 2, 0, 0, 0],
        "9x19mm AP 6.3": [6, 6, 6, 4, 2, 1],
        "9x19mm PBP gzh": [6, 6, 6, 5, 4, 3],
        "9x21mm PE gzh": [6, 2, 0, 0, 0, 0],
        "9x21mm P gzh": [6, 3, 0, 0, 0, 0],
        "9x21mm PS gzh": [6, 6, 3, 1, 0, 0],
        "9x21mm 7U4": [6, 6, 5, 3, 1, 0],
        "9x21mm BT gzh": [6, 6, 6, 4, 3, 1],
        '9x21mm 7N42 "Zubilo"': [6, 6, 6, 5, 4, 2],
        ".357 Magnum SP": [6, 1, 0, 0, 0, 0],
        ".357 Magnum HP": [6, 3, 0, 0, 0, 0],
        ".357 Magnum JHP": [6, 6, 2, 0, 0, 0],
        ".357 Magnum FMJ": [6, 6, 6, 2, 1, 0],
        ".45 ACP RIP": [1, 0, 0, 0, 0, 0],
        ".45 ACP Hydra-Shok": [6, 3, 0, 0, 0, 0],
        ".45 ACP Lasermatch FMJ": [6, 5, 1, 0, 0, 0],
        ".45 ACP Match FMJ": [6, 6, 3, 1, 0, 0],
        ".45 ACP AP": [6, 6, 6, 5, 4, 2],
        "4.6x30mm Action SX": [6, 5, 1, 0, 0, 0],
        "4.6x30mm Subsonic SX": [6, 6, 3, 0, 0, 0],
        "4.6x30mm JSP SX": [6, 6, 6, 4, 2, 1],
        "4.6x30mm FMJ SX": [6, 6, 6, 6, 4, 3],
        "4.6x30mm AP SX": [6, 6, 6, 6, 6, 5],
        "5.7x28mm R37.F": [4, 0, 0, 0, 0, 0],
        "5.7x28mm R37.X": [6, 1, 0, 0, 0, 0],
        "5.7x28mm SS198LF": [6, 4, 1, 0, 0, 0],
        "5.7x28mm SS197SR": [6, 6, 4, 1, 0, 0],
        "5.7x28mm SB193": [6, 6, 5, 2, 1, 0],
        "5.7x28mm L191": [6, 6, 6, 3, 2, 2],
        "5.7x28mm SS190": [6, 6, 6, 5, 4, 3],
        "5.45x39mm HP": [5, 0, 0, 0, 0, 0],
        "5.45x39mm PRS gs": [6, 1, 0, 0, 0, 0],
        "5.45x39mm SP": [6, 2, 0, 0, 0, 0],
        "5.45x39mm US gs": [6, 5, 1, 0, 0, 0],
        "5.45x39mm T gs": [6, 6, 1, 0, 0, 0],
        "5.45x39mm FMJ": [6, 6, 3, 2, 0, 0],
        "5.45x39mm PS gs": [6, 6, 5, 3, 1, 0],
        "5.45x39mm PP gs": [6, 6, 6, 4, 3, 1],
        "5.45x39mm BT gs": [6, 6, 6, 5, 3, 2],
        "5.45x39mm 7N40": [6, 6, 6, 6, 4, 3],
        "5.45x39mm BP gs": [6, 6, 6, 6, 5, 4],
        "5.45x39mm BS gs": [6, 6, 6, 6, 6, 5],
        '5.45x39mm PPBS gs "Igolnik"': [6, 6, 6, 6, 6, 6],
        "5.56x45mm Warmageddon": [1, 0, 0, 0, 0, 0],
        "5.56x45mm HP": [4, 0, 0, 0, 0, 0],
        "5.56x45mm MK 255 Mod 0 (RRLP)": [6, 1, 0, 0, 0, 0],
        "5.56x45mm M856": [6, 5, 1, 0, 0, 0],
        "5.56x45mm FMJ": [6, 6, 4, 1, 0, 0],
        "5.56x45mm M855": [6, 6, 5, 3, 2, 0],
        "5.56x45mm MK 318 Mod 0 (SOST)": [6, 6, 6, 4, 2, 1],
        "5.56x45mm M856A1": [6, 6, 6, 5, 3, 2],
        "5.56x45mm M855A1": [6, 6, 6, 6, 5, 4],
        "5.56x45mm M995": [6, 6, 6, 6, 6, 5],
        "5.56x45mm SSA AP": [6, 6, 6, 6, 6, 5],
        "6.8x51mm SIG FMJ": [6, 6, 6, 5, 4, 2],
        "6.8x51mm SIG Hybrid": [6, 6, 6, 6, 5, 5],
        ".300 Whisper": [6, 4, 2, 1, 0, 0],
        ".300 Blackout V-Max": [6, 6, 4, 3, 1, 0],
        ".300 Blackout BCP FMJ": [6, 6, 6, 3, 2, 0],
        ".300 Blackout M62 Tracer": [6, 6, 6, 5, 4, 2],
        ".300 Blackout CBJ": [6, 6, 6, 6, 5, 3],
        ".300 Blackout AP": [6, 6, 6, 6, 5, 4],
        "7.62x39mm HP": [6, 4, 1, 0, 0, 0],
        "7.62x39mm SP": [6, 6, 2, 0, 0, 0],
        "7.62x39mm FMJ": [6, 6, 4, 1, 0, 0],
        "7.62x39mm US gzh": [6, 6, 5, 3, 1, 0],
        "7.62x39mm T-45M1 gzh": [6, 6, 6, 3, 1, 0],
        "7.62x39mm PS gzh": [6, 6, 6, 5, 3, 2],
        "7.62x39mm PP gzh": [6, 6, 6, 6, 4, 3],
        "7.62x39mm BP gzh": [6, 6, 6, 6, 5, 4],
        "7.62x39mm MAI AP": [6, 6, 6, 6, 6, 5],
        "7.62x51mm Ultra Nosler": [6, 4, 0, 0, 0, 0],
        "7.62x51mm TCW SP": [6, 6, 6, 3, 2, 0],
        "7.62x51mm BCP FMJ": [6, 6, 6, 4, 3, 2],
        "7.62x51mm M80": [6, 6, 6, 6, 5, 4],
        "7.62x51mm M62 Tracer": [6, 6, 6, 6, 5, 5],
        "7.62x51mm M61": [6, 6, 6, 6, 6, 6],
        "7.62x51mm M993": [6, 6, 6, 6, 6, 6],
        "7.62x54mm R HP BT": [6, 6, 3, 1, 0, 0],
        "7.62x54mm R SP BT": [6, 6, 5, 4, 2, 1],
        "7.62x54mm R FMJ": [6, 6, 6, 5, 3, 2],
        "7.62x54mm R T-46M gzh": [6, 6, 6, 6, 4, 3],
        "7.62x54mm R LPS gzh": [6, 6, 6, 6, 4, 3],
        "7.62x54mm R PS gzh": [6, 6, 6, 6, 5, 5],
        "7.62x54mm R BT gzh": [6, 6, 6, 6, 6, 5],
        "7.62x54mm R SNB gzh": [6, 6, 6, 6, 6, 6],
        "7.62x54mm R BS gs": [6, 6, 6, 6, 6, 6],
        ".338 Lapua Magnum TAC-X": [6, 5, 3, 1, 0, 0],
        ".338 Lapua Magnum UCW": [6, 6, 6, 5, 4, 2],
        ".338 Lapua Magnum FMJ": [6, 6, 6, 6, 5, 5],
        ".338 Lapua Magnum AP": [6, 6, 6, 6, 6, 6],
        "9x39mm FMJ": [6, 5, 2, 0, 0, 0],
        "9x39mm SP-5 gs": [6, 6, 5, 2, 1, 0],
        "9x39mm SPP gs": [6, 6, 6, 5, 3, 2],
        "9x39mm PAB-9 gs": [6, 6, 6, 6, 5, 4],
        "9x39mm SP-6 gs": [6, 6, 6, 6, 5, 5],
        "9x39mm BP gs": [6, 6, 6, 6, 6, 5],
        ".366 TKM Geksa": [6, 3, 0, 0, 0, 0],
        ".366 TKM FMJ": [6, 6, 4, 1, 0, 0],
        ".366 TKM EKO": [6, 6, 6, 3, 1, 0],
        ".366 TKM AP-M": [6, 6, 6, 6, 5, 4],
        "12.7x55mm PS12A": [6, 0, 0, 0, 0, 0],
        "12.7x55mm PS12": [6, 6, 5, 2, 1, 0],
        "12.7x55mm PS12B": [6, 6, 6, 6, 5, 4],
        "12/70 5.25mm buckshot": [3, 3, 3, 3, 3, 3],
        "12/70 8.5mm Magnum buckshot": [3, 3, 3, 3, 3, 3],
        "12/70 6.5mm Express buckshot": [3, 3, 3, 3, 3, 3],
        "12/70 7mm buckshot": [3, 3, 3, 3, 3, 3],
        "12/70 Piranha": [6, 6, 5, 4, 4, 4],
        "12/70 flechette": [6, 6, 6, 5, 5, 5],
        "12/70 RIP": [0, 0, 0, 0, 0, 0],
        "12/70 SuperFormance HP slug": [0, 0, 0, 0, 0, 0],
        "12/70 Grizzly 40 slug": [6, 2, 0, 0, 0, 0],
        "12/70 Copper Sabot Premier HP slug": [6, 3, 1, 0, 0, 0],
        "12/70 lead slug": [6, 4, 1, 0, 0, 0],
        '12/70 "Poleva-3" slug': [6, 5, 1, 0, 0, 0],
        "12/70 Dual Sabot slug": [6, 5, 2, 0, 0, 0],
        "12/70 FTX Custom Lite slug": [6, 6, 2, 0, 0, 0],
        '12/70 "Poleva-6u" slug': [6, 6, 2, 0, 0, 0],
        "12/70 makeshift .50 BMG slug": [6, 6, 5, 3, 1, 0],
        "12/70 AP-20 armor-piercing slug": [6, 6, 6, 5, 4, 3],
        "20/70 5.6mm buckshot": [3, 3, 3, 3, 3, 3],
        "20/70 6.2mm buckshot": [3, 3, 3, 3, 3, 3],
        "20/70 7.5mm buckshot": [3, 3, 3, 3, 3, 3],
        "20/70 7.3mm buckshot": [3, 3, 3, 3, 3, 3],
        "20/70 Devastator slug": [1, 0, 0, 0, 0, 0],
        '20/70 "Poleva-3" slug': [6, 2, 0, 0, 0, 0],
        "20/70 Star slug": [6, 5, 1, 0, 0, 0],
        '20/70 "Poleva-6u" slug': [6, 5, 1, 0, 0, 0],
        "23x75mm Zvezda flashbang round": [0, 0, 0, 0, 0, 0],
        "23x75mm Shrapnel-25 buckshot": [6, 4, 3, 3, 3, 3],
        "23x75mm Shrapnel-10 buckshot": [6, 4, 3, 3, 3, 3],
        "23x75mm Barrikada slug": [6, 6, 6, 6, 4, 4],
        "40x46mm M576 (MP-APERS) grenade": [5, 3, 3, 3, 3, 3],
        "30x29mm VOG-30 E": [0, 0, 0, 0, 0, 0],
        "12.7x108mm BZT-44M": [6, 6, 6, 6, 6, 6],
        "12.7x108mm B-32": [6, 6, 6, 6, 6, 6],
    }

    if name in efficiency:
        return efficiency[name]
    return []
