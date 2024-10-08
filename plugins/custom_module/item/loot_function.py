import pendulum


def process_loot(item):
    """
    loot 데이터 가공
    """

    id = item.get("id")
    name_en = item.get("name")
    # name_kr = get_loot_kr(name_en)
    short_name = item.get("shortName")
    image = item.get("image512pxLink")
    category = (
        change_category(item["category"].get("name"), name_en) if item.get("category") else None
    )
    update_time = pendulum.now("Asia/Seoul")

    return (
        id,
        name_en,
        # name_kr,
        short_name,
        image,
        category,
        update_time,
    )


def change_category(category, name):
    """
    카테고리 변경
    """
    special_list = [
        "Portable Range Finder",
        "Radio Transmitter",
        "Repair Kits",
        "Compass",
        "Cultist Amulet",
    ]

    jewelry_list = [
        "Battered antique book",
        "Loot Lord plushie",
        'Old firesteel'
    ]

    lubricant_list = [
        'Gunpowder "Eagle"',
        'Gunpowder "Hawk"',
        'Gunpowder "Kite"',
        "Metal fuel tank",
        "Expeditionary fuel tank"
    ]

    if category in special_list:
        return "Special equipment"
    elif name in jewelry_list:
        return "Jewelry"
    elif name in lubricant_list:
        return "Lubricant"

    return category


def get_loot_kr(name):
    """
    전리품 한글 이름
    """
    kr_dict = {
        "42 Signature Blend English Tea": "42 시그니처 블렌드 잉글리시 티",
        "Apollo Soyuz cigarettes": "Apollo 아폴로 소유즈 담배",
        "Aramid fiber fabric": "Aramid 아라미드 원단",
        "BEAR Buddy plush toy": "BEAR Buddy 인형",
        "Pack of Arseniy buckwheat": "Pack of Arseniy buckwheat",
        "Can of Dr. Lupo's coffee beans": "Dr.Lupo의 커피 원두",
        "Can of Majaica coffee beans": "Majaica coffee 메자이카 커피",
        "Cordura polyamide fabric": "Cordura 코듀라 폴리아미드 원단",
        "Dogtag": "인식표",
        "Fleece fabric": "Fleece 플리스 원단",
        "FP-100 filter absorber": "FP-100 공기필터",
        "Gas mask air filter": "Filter 방독면 정화통",
        "Malboro Cigarettes": "Malboro 말보루 담배",
        "OFZ 30x165mm shell": "OFZ 30x160mm 포탄",
        "Paracord": "Paracord 낙하산 줄",
        "Press pass (issued for NoiceGuy)": "Press pass 기자 출입증",
        "Ripstop fabric": "Ripstop 립스톱 원단",
        "Strike Cigarettes": "Strike 스트라이크 담배",
        "UZRGM grenade fuze": "UZRGM 수류탄 신관",
        "Water filter": "Water filter 정수 필터",
        "Weapon parts": "Weapon parts 무기 부품",
        "Wilston cigarettes": "Wiliston 월스턴 담배",
        "Analog thermometer": "Analog thermometer 아날로그 온도계",
        "Bolts": "Bolts 볼트",
        "Corrugated hose": "Corrugated hose 주름진 호스",
        "Duct tape": "Duct tape 덕트 테이프",
        "Insulating tape": "Insulating tape 절연 테이프",
        "KEKTAPE duct tape": "KEKTAPE 덕트 테이프",
        "Metal spare parts": "Metal spare parts 금속 예비 부품",
        "Military corrugated tube": "Military tube 군용 주름진 튜브",
        "Pack of nails": "Nails 못 상자",
        "Pack of screws": "Screws 나사 한 봉지",
        "Piece of plexiglass": "Plexiglass 조각",
        "Pressure gauge": "Pressure gauge 압력게이지",
        "Screw nuts": "Screw nuts 너트",
        "Shustrilo sealing foam": "Shustrilo 슈스트릴로 실링 폼",
        "Silicone tube": "Silicone tube 실리콘 튜브",
        "Tube of Poxeram cold welding": "Poxeram 냉간 용접 접착제",
        "Xenomorph sealing foam": "Xenomorph 제노모프 실링 폼",
        "Broken GPhone X smartphone": "GPX GPhone X 고장난 스마트폰",
        "Broken GPhone smartphone": "GPhone 고장난 스마트폰",
        "Broken LCD": "Broken LCD 부서진 LCD",
        "Bundle of wires": "Wires 전선",
        "Capacitors": "Capacitors 축전기",
        "CPU fan": "CPU fan 쿨러",
        "Damaged hard drive": "HDD 손상된 하드 드라이브",
        "DVD drive": "DVD 드라이브",
        "Electric drill": "Electric drill 전동 드릴",
        "Electric motor": "Electric motor 전동 모터",
        "Electronic components": "Electronic components",
        "Energy-saving lamp": "ES Lamp 에너지 절약 램프",
        "Advanced current converter": "Advanced current converter",
        "Far-forward GPS Signal Amplifier Unit": "Far-forward GPS Signal Amplifier Unit",
        "Gas analyzer": "Gas analyzer 가스 분석기",
        "Geiger-Muller counter": "GMcount 가이거-뮐러 계수기",
        "Golden 1GPhone smartphone": "Golden 1GPhone 스마트폰",
        "Graphics card": "GPU 그래픽 카드",
        "Iridium military thermal vision module": "Iridium 군용 열화상 이리듐 모듈",
        "Light bulb": "Light bulb 전구",
        "Magnet": "Magnet 자석",
        "Microcontroller board": "Microcontroller board",
        "Military cable": "Military cable 군용 케이블",
        "Military circuit board": "MCB 군용 회로기판",
        "Military COFDM Wireless Signal Transmitter": "SG-C10 COFDM 군용 무선 신호 송신기",
        "Military gyrotachometer": "MGT 군용 자이로 측정기",
        "Military power filter": "Military power filter 군용 전력 필터",
        "NIXXOR lens": "NIXXOR 닉콘 렌즈",
        "PC CPU": "PC CPU",
        "Phase control relay": "Relay 위상 제어 계전기",
        "Phased array element": "AESA 위상 배열 부품",
        "Power cord": "Power cord 파워코드",
        "Power supply unit": "PSU 전원공급장치",
        "Printed circuit board": "PCB 인쇄 회로 기판",
        "Radiator helix": "Radiator helix 라디에이터 나선관",
        "RAM": "RAM",
        "Spark plug": "Spark plug 점화 플러그",
        "T-Shaped plug": "T-Shaped plug T자형 멀티탭",
        "Tetriz portable game console": "Tetriz 테트리즈 휴대용 게임기",
        "UHF RFID Reader": "UHF RFID 리더기",
        "Ultraviolet lamp": "UV Lamp 자외선 램프",
        "USB Adapter": "USB-A 어댑터",
        "Virtex programmable processor": "Virtex 프로그래밍 가능한 프로세서",
        "VPX Flash Storage Module": "VPX 플래시 저장소 모듈",
        "Working LCD": "Working LCD 작동하는 LCD",
        "6-STEN-140-M military battery": "Tank battery 6-STEN-140-M 탱크 배터리",
        "AA Battery": "AA 배터리",
        "Car battery": "Car battery 자동차 배터리",
        "Cyclon rechargeable battery": "Cyclon battery 충전지",
        "D Size battery": "D Size battery 0형 배터리",
        "GreenBat lithium battery": "GreenBat battery 리튬 배터리",
        "Portable Powerbank": "Powerbank 보조배터리",
        "Rechargeable battery": "Rechargeable battery 충전지",
        "Can of thermite": "Thermite 테르밋",
        "Classic matches": "Classic matches 클래식 성냥",
        "Crickent lighter": "Crickent 크리켄트 라이터",
        "Dry fuel": "Dry fuel 고체연료",
        "Expeditionary fuel tank": "Expeditionary fuel tank 여행용 연료통",
        "#FireKlean gun lube": "#Fireklean 총기 윤활유",
        "Fuel conditioner": "Fuel conditioner 연료 첨가제",
        'Gunpowder "Eagle"': 'Gunpowder "Eagle" 화약',
        'Gunpowder "Hawk"': 'Gunpowder "Hawk" 화약',
        'Gunpowder "Kite"': 'Gunpowder "Kite" 화약',
        "Hunting matches": "Hunting matches 사냥용 성냥",
        "Metal fuel tank": "Metal fuel tank 금속 연료통",
        "Propane tank (5L)": "Propane tank 프로판 탱크 (5L)",
        "SurvL Survivor Lighter": "SurvL 서바이벌 라이터",
        "TP-200 TNT brick": "TP-200 TNT 블록",
        "WD-40 (400ml)": "WD-40 (400ml)",
        "WD-40 100ml": "WD-40 (100ml)",
        "Zibbo lighter": "Zibbo lighter 지뽀 라이터",
        "Alkaline cleaner for heat exchangers": "Alkali 열 교환기용 알칼리 세제",
        "Can of white salt": "Can of white salt",
        "Clin window cleaner": "Clin 클린 창문 세정제",
        "Deadlyslob's beard oil": "Deadlysiob의 수염 기름",
        "LVNDMARK's rat poison": "LVNDMARK의 취약",
        "Ortodontox toothpaste": "Ortodontox 치약",
        "Ox bleach": "Ox bleach 옥스 표백제",
        "Pack of chlorine": "Chlorine 염소",
        "Pack of sodium bicarbonate": "Sadium 탄산 수소 나트륨",
        "PAID AntiRoach spray": "PAID 페이드 살충제",
        "Printer paper": "Printer paper 프린터 용지",
        "Repellent": "Repellent 방충제",
        "Schaman shampoo": "Schaman shampoo 샴푸",
        "Smoked Chimney drain cleaner": "Smoked Chimney 배수관 세정제",
        "Soap": "Soap 비누",
        "Toilet paper": "Tailet paper 화장지",
        "Toothpaste": "Toothpaste 치약",
        "Aquapeps water purification tablets": "Aquapeps water purification tablets",
        "Bottle of hydrogen peroxide": "H202 과산화수소",
        "Bottle of OLOLO Multivitamins": "OLOLO Multivitamins 종합 비타민",
        "Bottle of saline solution": "Nacl 생리식염수",
        "Disposable syringe": "Disposable syringe 일회용 주사기",
        "LEDX Skin Transilluminator": "LEDX 피부 트랜스일루미네이터",
        "Medical bloodset": "Bloodset 의료 채혈세트",
        "Medical tools": "Medical tools 의료 도구",
        "Ophthalmoscope": "Ophthalmoscope 검안경",
        "Pile of meds": "Pile of meds 약더미",
        "Portable defibrillator": "Portable defibrillator 휴대용 제세동기",
        "Awl": "Awl",
        "Bulbex cable cutter": "Bulbex 케이블 커터",
        "Construction measuring tape": "Measuring tape 건축용 출자",
        "Fierce Blow sledgehammer": "Fierce Blow sledgehammer",
        "Flat screwdriver": "Flat screwdriver 일자 드라이버",
        "Flat screwdriver (Long)": "Screwdriver 긴 일자 드라이버",
        "Hand drill": "Hand drill 핸드드릴",
        "Metal cutting scissors": "Metal cutting scissors 판금가위",
        "Nippers": "Nippers 니퍼",
        "Pipe grip wrench": "Pipe grip wrench 파이프 그립 렌치",
        "Pliers": "Pliers 플라이어",
        "Pliers Elite": "Pliers Elite 엘리트 플라이어",
        "Ratchet wrench": "Ratchet wrench 라쳇 렌치",
        "Round pliers": "Round pliers 원형 플라이어",
        "Screwdriver": "Screwdriver 드라이버",
        'Set of files "Master"': 'Set of files "Master"',
        "Sewing kit": "Sewing kit 재봉 키트",
        "Toolset": "Toolset 공구세트",
        "Wrench": "Wrench 렌치",
        "Antique teapot": "Antique teapot 골동품 찻주전자",
        "Antique vase": "Antique vase 골동품 꽃병",
        "Axel parrot figurine": "Axel 앵무새 조각상",
        "Battered antique book": "Battered antique book 낡은 골동품 책",
        "BEAR operative figurine": "BEAR 요원 피규어",
        "Bronze lion figurine": "Lion 청동 사자상",
        "Cat figurine": "Cat 고양이 조각상",
        "Chain with Prokill medallion": "Prokill 메달이 달린 목걸이",
        "Chainlet": "Chainlet 체인 목걸이",
        "Christmas tree ornament (Red)": "Christmas tree ornament (Red)",
        "Christmas tree ornament (Silver)": "Christmas tree ornament (Silver)",
        "Christmas tree ornament (Violet)": "Christmas tree ornament (Violet)",
        "Cultist figurine": "Cultist figurine",
        "Ded Moroz figurine": "제드 마로스 피규어",
        "Gold skull ring": "Gold skull ring 황금 해골 반지",
        "Golden egg": "Golden egg 황금알",
        "Golden neck chain": "Golden neck chain 금목걸이",
        "Golden rooster figurine": "Golden rooster 황금 수탉",
        "Horse figurine": "Horse 말 조각상",
        '"Lega" Medal': '"Lega" Medal',
        "Loot Lord plushie": "Loot Lord 인형",
        "Old firesteel": "old firesteel 오래된 부시",
        "Physical Bitcoin": "0.2BTC bitcoin 현물 비트코인",
        "Politician Mutkevich figurine": "Politician Mutkevich figurine",
        "Raven figurine": "Raven figurine 까마귀 동상",
        "Roler Submariner gold wrist watch": "Roler 롤러 서브마리너 골드 손목시계",
        "Ryzhy figurine": "Ryzhy 피규어",
        "Scav figurine": "Scav 스캐브 피규어",
        "Silver Badge": "Silver Badge 은 배지",
        "USEC operative figurine": "USEC 요원 피규어",
        "Veritas guitar pick": "Veritas 기타 피크",
        "Wooden clock": "Clock 나무 시계",
        "Advanced Electronic Materials textbook": "Advanced Electronic Materials textbook",
        "BakeEzy cook book": "BakeEzy 요리책",
        "Diary": "Diary 다이어리",
        "Intelligence folder": "Intelligence 정보 파일",
        "Military flash drive": "Military 군용 플래시 드라이브",
        "SAS drive": "SAS 드라이브",
        "Secure Flash drive": "USB 보안 플래시 드라이브",
        "Secure magnetic tape cassette": "SMT 보안 자기 테이프 카세트",
        "Silicon Optoelectronic Integrated Circuits textbook": "Silicon Optoelectronic Integrated Circuits textbook",
        "Slim diary": "Slim diary 얇은 다이어리",
        "SSD drive": "SSD 드라이브",
        "Tech manual": "Tech manual 기술 매뉴얼",
        'TerraGroup "Blue Folders" materials': 'TerraGroup "Blue Folders" materials',
        "Topographic survey maps": "Topographic survey maps",
        "Video cassette with the Cyborg Killer movie": "Cyborg Killer 사이보그 킬러 영화가 든 비디오카세트",
        "Body armor repair kit": "Body armor repair kit 방탄복 수리 키트",
        "Digital secure DSP radio transmitter": "Digital secure DSP radio transmitter",
        "EYE MK.2 professional hand-held compass": "EYE MK.2 전문가용 휴대용 나침반",
        "Leatherman Multitool": "Leatherman 멀티툴",
        "Mark of The Unheard": "Mark of The Unheard",
        "MS2000 Marker": "MS2000 마커",
        "Radio repeater": "Radio repeater",
        "Signal Jammer": "Signal Jammer 전파 교란기",
        "Sacred Amulet": "Sacred Amulet",
        "Vortex Ranger 1500 rangefinder": "Vortex Ranger 1500 거리 측정기",
        "WI-FI Camera": "WI-FI 카메라",
        "Weapon repair kit": "Weapon repair kit 무기 수리 키트",
    }

    if name in kr_dict:
        return kr_dict[name]

    return name
