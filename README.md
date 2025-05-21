- [EFT Library의 Airflow 운영 방식](#eft-library의-airflow-운영-방식)
  * [주요 사항](#주요-사항)
  * [패키지 정보](#패키지-정보)
  * [구조](#구조)
  * [흐름](#흐름)
  * [운영 중 발생한 문제 및 해결 과정](#운영-중-발생한-문제-및-해결-과정)
    + [1. 데이터 불일치 문제](#1-데이터-불일치-문제)
    + [2. 1일 단위 Upsert 문제](#2-1일-단위-upsert-문제)
    + [3. 다국어 데이터 매핑 및 처리 데이터 양 증가의 문제](#3-다국어-데이터-매핑-및-처리-데이터-양-증가의-문제)
    + [4. 불안정한 다국어 데이터의 처리](#4-불안정한-다국어-데이터의-처리)

# EFT Library의 Airflow 운영 방식

EFT Library는 [Tarkov Dev](https://tarkov.dev/api/) 에서 Airflow를 사용하여 주기적으로 데이터를 가져와 업데이트 합니다.

![architecture](https://github.com/user-attachments/assets/4e7b9a40-e298-430b-a7c7-8854bc5423f2)

## 주요 사항

- Tarkov Dev **API는 GraphQL 형식**이며, **Airflow에서 JSON 데이터를 요청**하여 가져온 후 **DB에 적재**합니다.
- DB Connection 정보는 **Airflow UI의 Config**를 사용합니다.
- 수작업을 최소화하기 위해, Tarkov Dev에서 데이터를 가져온 후 **필요한 부분만 수정**하는 방식을 채택했습니다.
- 데이터는 모두 영어이므로, **한글이나 일본어가 없는 경우 코드 내에서 변환**합니다. 예: 회복 아이템의 버프 및 디버프 정의
- DB 데이터 덤프는 매일 00:20에 실행되며, 아이템 시세와 같은 데이터가 많은 테이블은 제외 후 진행합니다.


## 패키지 정보

- Python 3.9
- Airflow 2.10.5

## 구조

- **dags**
  - **data dump** : DB Dump
  - **boss upsert** : 보스 정보 갱신
  - **hideout upsert** : 은신처 정보 갱신
  - **item upsert** : 아이템 정보 갱신
  - **quest item upsert** : 퀘스트 관련 아이템 정보 갱신
  - **item price upsert** : 아이템 현재 시세 정보 및 history 갱신 및 적재
  - **item price delete** : 아이템 시세 history 2주 지난 데이터는 삭제 처리
  - **quest upsert** : 퀘스트 갱신
  - **trader upsert** : NPC 상인 정보 갱신
  - **search update** : 메인 페이지 검색 기능 데이터 갱신
 
![airflow_main](https://github.com/user-attachments/assets/523a62e3-45c1-4d9c-9efd-d346b6ef4b39)


## 흐름

현재 Dag는 2가지 흐름으로 되어 있습니다.

대부분의 DAG는 **GraphQL API를 통해 일본어, 한국어, 영어 데이터를 각각 요청한 뒤**, 이를 개별 JSON 파일로 저장합니다.

이후 각 태스크에서 해당 파일들을 읽어 들여 언어별 데이터를 하나의 딕셔너리로 통합한 후, 이를 DB에 적재하는 방식으로 동작합니다.

![hiedout](https://github.com/user-attachments/assets/e5337b3e-7cbe-499d-b3b9-a5fc7dac1672)

DB 덤프와 같은 일부 DAG는 **BranchOperator를 사용하여 실행할 Task를 동적으로 선택**하는 방식을 사용합니다.

![스크린샷 2025-05-21 오전 9 20 51](https://github.com/user-attachments/assets/6cf84d60-7e56-43da-a59a-07cee0da86f0)


**첫번째 방식이 대부분 Dag의 흐름**이며, 두번째는 DB Data를 Dump 할 때만 사용하고 있습니다.

## 운영 중 발생한 문제 및 해결 과정

### 1. 데이터 불일치 문제  

Tarkov Dev **API에서 반환하는 데이터와 게임내의 데이터가 일치하지 않는 경우가 발생**하여, 수작업으로 조절하여 값을 넣어야 하는 경우가 많았습니다.  

**✔ 해결:**  
- Airflow Task 내부 함수에서 특정 값에 대한 보정 로직 추가

![different_data](https://github.com/user-attachments/assets/a1e838ea-22ce-4c0d-a235-bf7f45e85d0c)


### 2. 1일 단위 Upsert 문제  

DB에서 수작업으로 데이터를 변경해도, **다음 Upsert 실행 시 다시 덮어써지는 문제가 발생**했습니다.  

**✔ 해결:**  
- Upsert 과정에서 기존 데이터를 유지할 수 있도록 Task 내부 함수에서 수정했습니다.

### 3. 다국어 데이터 매핑 및 처리 데이터 양 증가의 문제  

API의 Graphql 형식에 따라 언어를 다르게 조회하려면 한번에 못하고 **개별로 요청**을 해야 했습니다. - **en, ko, ja**

또한 데이터가 3배가 되면서 xcom을 사용해 주고 받기에는 무리가 생겨 **json으로 임시 폴더에 저장을 했다가 각 task별로 파일을 읽은 뒤 데이터를 사용하는 방식**으로 수정 했습니다.

데이터를 읽은 뒤 동일한 id로 매핑을 해서 함수에 전달하는 방식을 적용했고, 함수에서 언어 데이터만 추가로 병합하는 과정을 진행했습니다.

**언어를 입력받아 요청하는 Json을 만드는 함수**

![get_lang](https://github.com/user-attachments/assets/39117784-784d-45a3-aeb8-91b377687aba)

**lang별 저장소 위치 선언**

![define_lang_data](https://github.com/user-attachments/assets/2c46b761-2d51-4d9d-8f08-147fbd9f42cc)

**API 응답결과 파일 저장**

![save_json](https://github.com/user-attachments/assets/ea648ce7-919b-49d0-a493-c3011c8c2baf)

**Task에서 json을 읽은 후 동일한 ID 데이터 Mapping 및 데이터 가공 함수에 전송**

![send_lang_data](https://github.com/user-attachments/assets/56b23d4d-5526-4a97-8af4-6aad694be06a)

**3개의 언어 데이터를 Mapping하여 반환**

![mapping_data](https://github.com/user-attachments/assets/69cb5a02-92bd-4eef-bfe4-b463a9ecb645)


**✔ 해결:**  
- 데이터를 언어별로 개별 요청하여 Json파일로 저장한 후 동일한 ID끼리 Mapping 하여 적재

### 4. 불안정한 다국어 데이터의 처리  

다국어 데이터를 받아오지만 데이터 자체가 아직 **미번역되어 영어로 된 데이터가 많아**서 해당 값들은 **코드내에서 수정**하는 방식을 사용했습니다.

![not_translate](https://github.com/user-attachments/assets/16d34905-c981-485f-9b19-e5f42ef8bb76)


**✔ 해결:**  
- 데이터 매핑을 만들어 일정 부분 자동화를 진행했습니다.    

**문제점:**
- 새로운 영문명이 추가될 때마다 업데이트 필요합니다  
- **고지능의 AI를 사용하지 않는 한 완전 자동화는 어려운 영역인 것 같습니다. (AI가 번역한 것과 게임 내의 단어가 다른 경향이 다수 존재)**



