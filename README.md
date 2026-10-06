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

- Airflow는 **Tarkov Dev JSON API(`https://json.tarkov.dev`)에서 데이터를 가져온 후 DB에 적재**합니다. 공통 클라이언트는 `plugins/custom_module/tarkov_json_api.py`입니다.
- DB Connection 정보는 **Airflow UI의 Config**를 사용합니다.
- 수작업을 최소화하기 위해, Tarkov Dev에서 데이터를 가져온 후 **필요한 부분만 수정**하는 방식을 채택했습니다.
- 데이터는 모두 영어이므로, **한글이나 일본어가 없는 경우 코드 내에서 변환**합니다. 예: 회복 아이템의 버프 및 디버프 정의
- DB 데이터 덤프는 매일 00:20에 실행되며, 아이템 시세와 같은 데이터가 많은 테이블은 제외 후 진행합니다.


## DAG 실패 알림

- 모든 DAG는 재시도 종료 후 실행이 최종 실패하면 `smtp_gmail` 연결로 `poeynus@gmail.com`, `moonjipsa@gmail.com`에 메일을 보냅니다.
- 메일에는 DAG ID, Run ID, 시작·종료 시간과 실패 사유가 포함됩니다. 기존 서비스 이상 및 데이터 변경 메일은 유지됩니다.
- 공통 구현은 `plugins/custom_module/dag_failure_alert.py`입니다. `watch_dag_failure` 태스크가 모든 기존 태스크의 실패를 감시하여 정리 작업(`all_done`)이 성공해도 실패 상태가 유지됩니다.
- 새 DAG에도 `on_failure_callback=send_dag_failure_email`을 지정하고, 모든 태스크 정의 후 `add_failure_watcher(dag)`를 호출해야 합니다.
- Airflow UI/CLI에서 수동으로 실패 상태를 지정하는 경우에는 콜백이 실행되지 않습니다. 콜백 메일 전송 오류는 DAG processor 로그에서 확인합니다.

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

## 흐름

현재 Dag는 2가지 흐름으로 되어 있습니다.

데이터 수집 DAG는 **JSON API에서 원본 데이터와 필요한 언어(일본어, 한국어, 영어)의 번역 데이터를 가져와 결합한 뒤**, 이를 JSON 파일로 저장합니다.

이후 각 태스크에서 해당 파일들을 읽어 들여 언어별 데이터를 하나의 딕셔너리로 통합한 후, 이를 DB에 적재하는 방식으로 동작합니다.

<img width="902" height="888" alt="스크린샷 2026-01-29 오전 7 37 01" src="https://github.com/user-attachments/assets/5dbb6317-85c5-426f-8c36-8ff83255abbe" />

DB 덤프와 같은 일부 DAG는 **BranchOperator를 사용하여 실행할 Task를 동적으로 선택**하는 방식을 사용합니다.

<img width="1277" height="337" alt="스크린샷 2026-01-29 오전 7 37 21" src="https://github.com/user-attachments/assets/815b1833-981d-4fd8-b829-292a81222f42" />

**첫번째 방식이 대부분 Dag의 흐름**이며, 두번째는 DB Data를 Dump와 System Health Check에서 사용하고 있습니다.

## 개발 History

여기에서 확인해 주세요!

[velog 바로가기](https://velog.io/@poeynus/series/Airflow-%EA%B0%9C%EB%B0%9C)



### V3 시즌 가격 수집

- `v3_dags_item_price`는 PVP/PVE와 `pvp-season`을 수집합니다. 시즌 API와 아이템
  응답 검증이 끝난 뒤 시즌 메타데이터, 현재 가격, 상인 가격, 히스토리를 한
  트랜잭션으로 저장합니다. 이전 시즌 가격과 시즌 히스토리는 보존합니다.
- PVP/PVE의 `season_id`는 NULL이며, 기존 14일 히스토리 보관 정책을 유지합니다.
- 커밋 성공 후 `v3_dags_price_static_json`을 트리거합니다. 정적 JSON DAG의 독립
  시간 스케줄은 제거했으며 수동 실행도 가능합니다. 정적 JSON은 현재 시즌만
  포함하고 `pvp-season` 키와 `selected_season_id`를 제공합니다. 지난 시즌 조회는
  백엔드 API의 `season_id`/`seasonId`를 사용합니다.
- 배포 시 기존 가격 수집 DAG를 중지하고 백엔드의
  `sql/migrations/20261007_price_seasons.sql`을 먼저 적용한 뒤 새 DAG를 배포해야
  합니다. 새 충돌 키는 마이그레이션 이전 DB와 호환되지 않습니다. 시험 적재와
  API 조회를 확인한 다음 DAG를 재개하고 정적 JSON을 재생성합니다.
- 로컬 회귀 검사: `python3 -m unittest discover -s tests -v`
