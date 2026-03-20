- [타르코프 도서관의 운영 방식](#타르코프-도서관의-운영-방식)
  * [주요 사항](#주요-사항)
  * [패키지 정보](#패키지-정보)
  * [구조](#구조)
  * [흐름](#흐름)
  * [개발 History](#개발-History)

# 타르코프 도서관의 운영 방식

타르코프 도서관은 [Tarkov Dev](https://tarkov.dev/api/) 에서 Airflow를 사용하여 주기적으로 데이터를 가져와 업데이트 합니다.

<img width="1314" height="1275" alt="arch_v4" src="https://github.com/user-attachments/assets/0392b55e-14b0-45d8-9aa6-4b83a9cd640f" />

## 주요 사항

- Tarkov Dev **API는 GraphQL 형식**이며, **Airflow에서 JSON 데이터를 요청**하여 가져온 후 **DB에 적재**합니다.
- DB Connection 정보는 **Airflow UI의 Config**를 사용합니다.
- 수작업을 최소화하기 위해, Tarkov Dev에서 데이터를 가져온 후 **필요한 부분만 수정**하는 방식을 채택했습니다.
- 데이터는 모두 영어이므로, **한글이나 일본어가 없는 경우 코드 내에서 변환**합니다. 예: 회복 아이템의 버프 및 디버프 정의
- DB 데이터 덤프는 매일 00:20에 실행되며, 아이템 시세와 같은 데이터가 많은 테이블은 제외 후 진행합니다.
- LLM에 사용할 Rag에 적재하는 Vector Data는 기존의 모든 Task가 끝난 후 실행 됩니다.


## 패키지 정보

- Python 3.13
- Airflow 3.1.5

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
  - **health check** : 서비스 Health Check
  - **issue posts update** : 커뮤니티 인기글 데이터 갱신
  - **rag data update** : LLM에 사용할 Vector 데이터 갱신
  - **rag search update** : RAG 데이터 기준, 채팅창 자동완성 데이터 갱신

## 흐름

현재 Dag는 2가지 흐름으로 되어 있습니다.

대부분의 DAG는 **GraphQL API를 통해 일본어, 한국어, 영어 데이터를 각각 요청한 뒤**, 이를 개별 JSON 파일로 저장합니다.

이후 각 태스크에서 해당 파일들을 읽어 들여 언어별 데이터를 하나의 딕셔너리로 통합한 후, 이를 DB에 적재하는 방식으로 동작합니다.

<img width="902" height="888" alt="스크린샷 2026-01-29 오전 7 37 01" src="https://github.com/user-attachments/assets/5dbb6317-85c5-426f-8c36-8ff83255abbe" />

DB 덤프와 같은 일부 DAG는 **BranchOperator를 사용하여 실행할 Task를 동적으로 선택**하는 방식을 사용합니다.

<img width="1277" height="337" alt="스크린샷 2026-01-29 오전 7 37 21" src="https://github.com/user-attachments/assets/815b1833-981d-4fd8-b829-292a81222f42" />

**첫번째 방식이 대부분 Dag의 흐름**이며, 두번째는 DB Data를 Dump와 System Health Check에서 사용하고 있습니다.

## 개발 History

여기에서 확인해 주세요!

[velog 바로가기](https://velog.io/@poeynus/series/Airflow-%EA%B0%9C%EB%B0%9C)


