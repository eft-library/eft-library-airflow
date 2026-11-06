# KORD BREACH 수동 데이터 → 원천 ID 이전

현재 운영 공개 API의 40개 특성과 원천 KORD BREACH의 40개 특성을 영문 이름으로
대조해 확정한 매핑입니다. 실행 시점 DB가 다르면 SQL의 사전 검사에서 중단합니다.
사용자 프리셋의 실제 내용은 운영에서 조회하지 않았으며, 보존 동작은 임시 DB에서 검증했습니다.

## 이전 범위

- `kord_breach_modifier.id`: 문자열 slug → 원천 perk ID
- `kord_breach_modifier_conflict`: 양쪽 ID 변경, 기존 reason 보존
- `user_kord_breach_preset_modifier.modifier_id`: 같은 특성의 원천 ID로 변경
- `user_kord_breach_preset`: 이름·슬롯 유지, 저장된 총점 재계산
- 번역·설명·점수·아이콘·충돌 목록은 이후 DAG 실행으로 최신 원천에 동기화

테이블을 삭제하지 않습니다. 미확인 ID, 누락 항목, ID 충돌, 잘못 연결된 참조가 있으면
전체 이전을 중단합니다. 네 테이블을 같은 트랜잭션에서 잠그고 변경합니다.
잠금 획득은 최대 10초, SQL 문장 실행은 최대 60초로 제한합니다.
성공한 SQL은 다시 실행해도 같은 ID를 유지합니다.

## 운영 적용 순서

1. KORD BREACH 프리셋 저장이 적은 시간에 적용합니다. 새 DAG는 아직 비활성화합니다.
2. 사용하는 DB 접속 설정으로 네 테이블의 데이터를 백업합니다. 아래 `platform_db`는
   실제 데이터베이스 이름에 맞춥니다. 비밀번호를 명령문에 적을 필요는 없습니다.

```sh
pg_dump --dbname=platform_db --data-only \
  --table=kord_breach_modifier \
  --table=kord_breach_modifier_conflict \
  --table=user_kord_breach_preset \
  --table=user_kord_breach_preset_modifier \
  --file=kord_breach_before_source_ids.sql
```

3. SQL을 실행합니다. 알 수 없는 ID 등으로 실패하면 매핑을 검토하고, 검사 조건을
   삭제하거나 테이블을 비워서 우회하지 않습니다.

```sh
psql --dbname=platform_db -v ON_ERROR_STOP=1 \
  --file=sql/migrations/20261106_kord_breach_source_ids.sql
```

4. 결과의 `canonical_modifiers`가 40인지 확인합니다.
5. DAG와 `plugins/custom_module/kord_breach.py`, `kord_breach_mapping.json`,
   `queries/kord_breach.py`를 함께 배포합니다. 기존 `platform_db` Airflow Connection을 사용합니다.
6. `dags_kord_breach`를 수동 실행합니다. 성공하면 매일 한국 시간 02:45 일정으로 활성화합니다.
7. `/api/kord-breach/v3/modifiers`에서 40개 특성과 원천 ID·효과·아이콘을 확인하고,
   기존 사용자 프리셋의 조회와 선택 복원을 확인합니다. 원천의 새 충돌 조건에 어긋나는
   기존 선택은 자동 삭제하지 않으며 별도 검토합니다.
8. 프론트 특성 API 캐시가 300초이므로 캐시를 무효화하거나 만료 후 페이지를 새로고침합니다.
   기존 페이지에 이미 열린 선택 상태에는 이전 ID가 남아 있을 수 있습니다.

SQL은 ID 참조만 이전하므로, DAG 실행 전에 이미 기존 데이터로 화면 조회는 가능합니다.
DAG가 실패하더라도 이전된 ID와 기존 내용은 남습니다. 실패한 동기화의 부분 변경은 롤백됩니다.
백업에는 사용자 프리셋이 포함되므로 운영 데이터로 관리합니다. 복구가 필요하면
DAG를 비활성화하고, 백업 이후의 사용자 변경을 확인한 뒤 네 테이블을 함께 복구합니다.

## 정기 유지 정책

- 원천은 `pvp-season/season`과 언어별 `season_en`, `season_ko`, `season_ja`입니다.
- 현재 시즌 ID를 고정해 다른 시즌으로 자동 교체하지 않습니다.
- 원천 ID·공통/개인 구분·점수·충돌 대상의 일관성을 검증합니다.
- 분류(global/positive/negative), 정렬, 활성 상태는 기존 DB 설정을 보존합니다.
  빈 DB를 초기 적재하는 경우 검토된 매핑의 분류·정렬을 사용합니다.
- 누락된 한글·일본어 번역은 기존 값을 유지하며, 영어 원문이나 필수 구조가 없으면 실패합니다.
- 기존 충돌 사유는 해당 관계가 유지될 때 보존합니다. 새 관계의 reason은 NULL입니다.
- 원천 특성이 추가·삭제되면 먼저 중단하고 매핑을 검토합니다. 단순 점수 부호로
  분류를 추정하거나 사용자 선택을 삭제하지 않습니다.
- 점수 변경 시 저장된 프리셋 총점도 같은 트랜잭션에서 재계산합니다.
- HTTP API 응답 필드와 기존 `/v3` URL은 변경하지 않습니다. 새 정적 JSON DAG는 추가하지 않습니다.

## 매핑과 SQL 재생성

검토된 매핑은 `plugins/custom_module/kord_breach_mapping.json`에 있습니다.
이름 변경에 따른 매번의 추정 매칭 대신 원천 ID를 기준으로 동기화합니다.
SQL을 재생성할 때만 다음 명령을 사용합니다. 이 명령은 DB에 연결하지 않습니다.

```sh
python3 scripts/build_kord_breach_migration.py
```

SQL은 현재 `platform_db.sql`의 FK 없는 ID 참조 구조에 맞춰 검증했습니다.
운영에서 추가 FK나 트리거를 별도로 적용했다면 실제 제약도 확인해야 합니다.
