# EFT Library의 Airflow 운영 방식

EFT Library는 [Tarkov Dev](https://tarkov.dev/api/) 에서 Airflow를 사용하여 주기적으로 데이터를 가져와 업데이트 합니다.

![architecture](https://github.com/user-attachments/assets/e14049e2-188a-4166-8494-2c2ded7cfbc3)



## 주요 사항

- Tarkov Dev **API는 GraphQL 형식**이며, **Airflow에서 JSON 데이터를 요청**하여 가져온 후 **DB에 적재**합니다.
- 수작업을 최소화하기 위해, Tarkov Dev에서 데이터를 가져온 후 **필요한 부분만 수정**하는 방식을 채택했습니다.
- 데이터는 모두 영어이므로, **한글이나 일본어가 없는 경우 코드 내에서 변환**합니다. 예: 회복 아이템의 버프 및 디버프 정의
- DB 데이터 덤프는 매일 00:20에 실행되며, 아이템 시세와 같은 데이터가 많은 테이블은 제외 후 진행합니다.


## 환경 및 패키지 정보

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
 
![스크린샷 2025-02-10 오전 9 09 27](https://github.com/user-attachments/assets/6b36e8ab-03fe-4bee-8b27-923fec0d2f5a)


## 흐름

현재 Dag는 2가지 흐름으로 되어 있습니다.

대부분의 DAG는 **GraphQL API를 통해 일본어, 한국어, 영어 데이터를 각각 요청한 뒤**, 이를 개별 JSON 파일로 저장합니다.

이후 각 태스크에서 해당 파일들을 읽어 들여 언어별 데이터를 하나의 딕셔너리로 통합한 후, 이를 DB에 적재하는 방식으로 동작합니다.

![flow1](https://github.com/user-attachments/assets/36c56423-a362-4266-a3cc-a9838f2bfa07)

DB 덤프와 같은 일부 DAG는 **BranchOperator를 사용하여 실행할 Task를 동적으로 선택**하는 방식을 사용합니다.

![flow2](https://github.com/user-attachments/assets/b25d9ebe-6b87-49dc-be4c-267700580694)


**첫번째 방식이 대부분 Dag의 흐름**이며, 두번째는 DB Data를 Dump 할 때만 사용하고 있습니다.

## 운영 중 발생한 문제 및 해결 과정

### 1. 데이터 불일치 문제  

Tarkov Dev **API에서 반환하는 데이터와 게임내의 데이터가 일치하지 않는 경우가 발생**하여, 수작업으로 조절하여 값을 넣어야 하는 경우가 많았습니다.  

**✔ 해결:**  
- Airflow Task 내부 함수에서 특정 값에 대한 보정 로직 추가
- ![스크린샷 2025-01-31 오전 10 54 00](https://github.com/user-attachments/assets/a49fed2f-4a83-424e-a82c-db3dc54e5d55)


### 2. 1일 단위 Upsert 문제  

DB에서 수작업으로 데이터를 변경해도, 다음 Upsert 실행 시 다시 덮어써지는 문제가 발생했습니다.  

**✔ 해결:**  
- Upsert 과정에서 기존 데이터를 유지할 수 있도록 Task 내부 함수에서 수정했습니다.

### 3. 다국어 데이터 매핑 및 처리 데이터 양 증가의 문제  

API의 Graphql 형식에 따라 언어를 다르게 조회하려면 한번에 못하고 개별로 요청을 해야 했습니다. - en, ko, ja

또한 데이터가 3배가 되면서 xcom을 사용해 주고 받기에는 무리가 생겨 json으로 임시 폴더에 저장을 했다가 각 task별로 파일을 읽은 뒤 데이터를 사용하는 방식으로 수정 했습니다.

데이터를 읽은 뒤 동일한 id로 매핑을 해서 함수에 전달하는 방식을 적용했고, 함수에서 언어 데이터만 추가로 병합하는 과정을 진행했습니다.



**✔ 해결:**  
- 데이터 매핑 자동화를 적용하여 해결했으나, 좀 더 효율적인 방법이 필요하다고 생각합니다.
- ![스크린샷 2025-01-31 오전 10 51 54](https://github.com/user-attachments/assets/5775d0b7-981d-4b2a-8d64-d5f25d05a66f)
- ![스크린샷 2025-01-31 오전 10 52 33](https://github.com/user-attachments/assets/6e900826-9e74-4096-88f7-addc4d213fe3)

### 4. 불안정한 다국어 데이터의 처리  

다국어 데이터를 받아오지만 데이터 자체가 아직 미번역되어 영어로 된 데이터가 많아서 해당 값들은 코드내에서 수정하는 방식을 사용했습니다.

**✔ 해결:**  
- 데이터 매핑을 만들어 일정 부분 자동화를 진행했습니다.    

**문제점:**
- 새로운 영문명이 추가될 때마다 업데이트 필요합니다  
- **고지능의 AI를 사용하지 않는 한 완전 자동화는 어려운 영역인 것 같습니다. (AI가 번역한 것과 게임 내의 단어가 다른 경향이 다수 존재)**



