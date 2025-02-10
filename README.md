# EFT Library의 Airflow 운영 방식

EFT Library는 [Tarkov Dev](https://tarkov.dev/api/) 에서 주기적으로 데이터를 가져와 업데이트 한다.

이 페이지는 Airflow에 대하여 설명한다.

![airflow](https://github.com/user-attachments/assets/800b7340-4d64-4b7f-af61-6dc17e937f8f)



## 주요 사항

- Tarkov Dev **API는 GraphQL 형식**이며, **Airflow에서 JSON 데이터를 요청**하여 가져온 후 **DB에 적재**한다.
- 수작업을 최소화하기 위해, Tarkov Dev에서 데이터를 가져온 후 **필요한 부분만 수정**하는 방식을 채택했다.
- 데이터는 모두 영어이므로, **한글로 자동 변환**한다. 예: 회복 아이템의 버프 및 디버프 정의
- Next.js의 **SSG 방식 렌더링을 고려**하여, 데이터 변경이 바로 반영되지 않는 문제를 해결하기 위해 **DAG에서 매일 08:00에 Front를 Reboot**한다.
- DB 데이터 덤프는 매일 00:20에 실행된다.


## 환경

- Rocky Linux 8
- Python 3.9
- Airflow 2.9.1

## 구조

- **dags**
  - **data dump** : DB Dump
  - **server rebuild** : Front Reboot
  - **hideout upsert** : 은신처 정보 갱신
  - **item upsert** : 모든 아이템 정보 갱신
  - **quest item upsert** : 퀘스트 관련 아이템 정보 갱신
  - **quest upsert** : 퀘스트 갱신
  - **search update** : 메인 페이지 검색 기능 데이터 갱신
- **plugins**
  - **hideout** : 모든 은신처 관련 함수들
  - **item** : 모든 아이템 관련 함수들
  - **data dump** : DB Data Dump 관련 함수
  - **quest item** : 퀘스트 아이템 관련 함수
  - **boss** : 보스 관련 함수
  - **quest** : 퀘스트 관련 함수
 
![스크린샷 2025-02-10 오전 9 09 27](https://github.com/user-attachments/assets/6b36e8ab-03fe-4bee-8b27-923fec0d2f5a)


## 흐름

현재 Dag는 2가지 흐름으로 되어 있다.

대부분의 DAG는 GraphQL **API를 통해 데이터를 요청한 후**, 여러 개의 **Task로 분리하여 처리한 후 DB에 적재**하는 방식을 따른다.

![flow1](https://github.com/user-attachments/assets/36c56423-a362-4266-a3cc-a9838f2bfa07)


DB 덤프와 같은 일부 DAG는 **BranchOperator를 사용하여 실행할 Task를 동적으로 선택**하는 방식을 사용한다.

![flow2](https://github.com/user-attachments/assets/b25d9ebe-6b87-49dc-be4c-267700580694)


**첫번째 방식이 대부분 Dag의 흐름**이며, 두번째는 DB Data를 Dump 할 때만 사용하고 있다.

## 운영 중 발생한 문제 및 해결 과정

### 1. 데이터 불일치 문제  

Tarkov Dev **API에서 반환하는 데이터와 게임내의 데이터가 일치하지 않는 경우가 발생**하여,  
수작업으로 조절하여 값을 넣어야 하는 경우가 많음.  

**✔ 해결:**  
- Airflow Task 내부 함수에서 특정 값에 대한 보정 로직 추가
- ![스크린샷 2025-01-31 오전 10 54 00](https://github.com/user-attachments/assets/a49fed2f-4a83-424e-a82c-db3dc54e5d55)


### 2. 1일 단위 Upsert 문제  

DB에서 수작업으로 데이터를 변경해도, 다음 Upsert 실행 시 다시 덮어써지는 문제가 발생.  

**✔ 해결:**  
- Upsert 과정에서 기존 데이터를 유지할 수 있도록 Task 내부 함수에서 수정

### 3. 데이터 매핑 문제  

- **Ammo**의 `Round Type` 정보가 다르게 제공됨 → 직접 매핑 함수(`get_round()`) 작성  
- **Medical** 버프/디버프 값이 일관되지 않음 → 수동으로 매핑 작업 진행  

**✔ 해결:**  
- 데이터 매핑 자동화를 적용하여 해결했으나, 좀 더 효율적인 방법이 필요
- ![스크린샷 2025-01-31 오전 10 51 54](https://github.com/user-attachments/assets/5775d0b7-981d-4b2a-8d64-d5f25d05a66f)
- ![스크린샷 2025-01-31 오전 10 52 33](https://github.com/user-attachments/assets/6e900826-9e74-4096-88f7-addc4d213fe3)

### 4. 한글 변환 작업의 어려움  

영문명들을 한글로 변환해야 하지만, 자동화하기 어려워 현재는 수작업으로 처리.  

**✔ 해결:**  
- 데이터 매핑을 만들어 일정 부분 자동화 진행  
- 새로운 영문명이 추가될 때마다 업데이트 필요  
- **AI를 사용하지 않는 한 완전 자동화는 어려운 영역인 것 같음**  






