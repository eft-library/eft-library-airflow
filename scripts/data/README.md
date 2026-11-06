# 초기 ID 이전 자료

`kord_breach_legacy_mapping.json`은 기존 문자열 ID를 원천 ID로 바꾸는 최초 SQL을
재생성할 때만 사용하는 과거 매핑입니다. 새 원천 항목을 이 파일에 추가할 필요가 없습니다.

정기 `dags_kord_breach`와 `plugins/custom_module/kord_breach.py`에서는 이 파일을 읽지 않습니다.
운영 DAG 배포에 필요하지 않으며 최초 이전 후 삭제해도 정기 수집에는 영향이 없습니다.
다만 삭제하면 `scripts/build_kord_breach_migration.py`의 초기 SQL 재생성에는 사용할 수 없습니다.
