insert into tkl_search (value, link, page_value, type, "order")
    (select *, row_number() OVER () AS seq_num
     from (select '타르코프 지도 : ' || name_kr, '/map-of-tarkov/' || id, id, 'MAP_OF_TARKOV'
           from tkl_map_parent
           union all
           select '대화형 지도 : ' || name_kr, '/map/' || id, id, 'MAP'
           from tkl_map_parent
           union all
           select '보스 : ' || tkl_boss.name_kr, '/boss/' || id, id, 'BOSS'
           from tkl_boss
           union all
           select '하이드아웃 : ' || name_en, '/hideout', id, 'HIDEOUT'
           from tkl_hideout_master
           union all
           select '하이드아웃 : ' || name_kr, '/hideout', id, 'HIDEOUT'
           from tkl_hideout_master
           union all
           select '퀘스트 : ' || name_kr, '/quest/detail/' || id, id, 'QUEST'
           from tkl_quest
           union all
           select '퀘스트 : ' || name_en, '/quest/detail/' || id, id, 'QUEST'
           from tkl_quest
           union all
           select '상인 : ' || tkl_npc.name_kr, '/quest', id, 'TRADER'
           from tkl_npc
           union all
           select '무기 : ' || name, '/weapon?id=' || id, id, 'WEAPON'
           from tkl_weapon
           union all
           select '무기 : ' || name, '/weapon?id=' || id, id, 'WEAPON'
           from tkl_throwable
           union all
           select '무기 : ' || name, '/weapon?id=' || id, id, 'WEAPON'
           from tkl_knife
           union all
           select '탄약 : ' || name, '/ammo?id=' || id, id, 'AMMO'
           from tkl_ammo
           union all
           select '방탄모 : ' || name, '/head-wear?id=' || id, id, 'HEADWEAR'
           from tkl_headwear
           union all
           select '전술 조끼 : ' || name, '/rig?id=' || id, id, 'RIG'
           from tkl_rig
           union all
           select '방탄 조끼 : ' || name, '/armor-vest?id=' || id, id, 'ARMOR_VEST'
           from tkl_armor_vest
           union all
           select '헤드셋 : ' || name, '/headset?id=' || id, id, 'HEADSET'
           from tkl_headset
           union all
           select '가방 : ' || name, '/backpack?id=' || id, id, 'BACKPACK'
           from tkl_backpack
           union all
           select '의료품 : ' || name_kr, '/medical?id=' || id, id, 'MEDICAL'
           from tkl_medical
           union all
           select '컨테이너 : ' || name_kr, '/container?id=' || id, id, 'CONTAINER'
           from tkl_container
           union all
           select '키 : ' || name, '/key?id=' || id, id, 'KEY'
           from tkl_key
           union all
           select '식량 : ' || name_kr, '/provisions?id=' || id, id, 'PROVISIONS'
           from tkl_provisions
           union all
           select '전리품 : ' || name_kr, '/loot?id=' || id, id, 'LOOT'
           from tkl_loot
           union all
           select '얼굴 커버 : ' || name, '/face-cover?id=' || id, id, 'FACE_COVER'
           from tkl_face_cover
           union all
           select '완장 : ' || name, '/arm-band?id=' || id, id, 'ARM_BAND'
           from tkl_arm_band
           union all
           select '안경 : ' || name, '/glasses?id=' || id, id, 'GLASSES'
           from tkl_glasses
           ) as a)