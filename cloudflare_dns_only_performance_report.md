# Cloudflare DNS Only 전환 성능 분석 보고서

## 1. Executive Summary

Airflow 로그에서 정적 JSON 생성 작업의 큰 단축이 확인됐다. `v3_dags_item_static_json`의 2026-09-14 수동 실행은 **3,317.48초(55분 17초)**, 2026-10-03 수동 실행은 **287.45초(4분 47초)**였다. 실행시간은 **91.3% 감소**했다. DB `response_time`의 헬스체크 평균도 전후 5일 비교에서 FastAPI **1,020ms → 43ms(95.8% 감소)**, Next.js **3,339ms → 300ms(91.0% 감소)**로 낮아졌다. 각각 5,548건과 5,671건의 API 호출 결과를 생성했으므로, 단순히 처리량이 줄어서 빨라진 것은 아니다. 2026-08-06의 또 다른 전환 전 실행도 3,262.17초였다.

사용자가 제공한 전환 시각은 **2026-09-27 22:00 KST**다. 9월 27일 새벽까지 느렸던 다수의 static DAG가 9월 28일 새벽부터 빠르게 실행됐다. 예를 들어 퀘스트 static의 성공 실행은 9월 27일 315.79초였고, 10월 3일 성공한 수동 시도는 27.58초였다. 구간은 사용자 제공 시각을 기준으로 나눴다. Cloudflare 감사 로그로 이 시각을 독립 검증하지는 못했다. 실행시간의 개선은 로그로 확인됐지만, Cloudflare 경로의 어느 부분이 병목이었는지는 Nginx·FastAPI 운영 로그가 없어 확정할 수 없다.

우선 권장하는 개선은 Airflow의 FastAPI 호출을 내부 네트워크 주소로 전환하는 것이다. 그 전에 동일 endpoint를 공인 도메인과 내부 주소로 각각 측정하고, Nginx의 `request_time` 및 `upstream_response_time`을 보존해 병목 위치를 확인해야 한다.

## 2. 분석 환경

- 분석 위치: 로컬 Mac에 제공된 `logs/`와 Airflow·FastAPI 소스. 운영 서버에 직접 접속하지 않았다.
- 로그 규모: Airflow 태스크 로그 **51,143개, 약 1.42 GB**. 그중 static JSON DAG 로그는 **2,317개 시도 파일**이며, 이 숫자에는 API를 호출하지 않는 가격 static DAG도 포함된다. 파일 수는 DAG 실행 수와 다르다. 재시도마다 파일이 생긴다.
- 분석 기간: 제공된 static DAG 로그의 2026년 8월~10월 3일. 비교 구간은 태스크 로그 첫 이벤트의 **한국 시간** 기준 `2026-09-27 22:00` 이전과 이후로 나눴다. 이 전환 시각은 사용자 제공 정보다.
- 사용 자료: `logs/dag_id=v3_dags_*static_json/`, `dags/v3_dags_*static_json.py`, `dags/dags_health_check.py`, `plugins/custom_module/static_api_client.py`, 인접 백엔드 저장소의 `util/middleware.py`, `api/dashboard/query.py`와 Git 변경 이력. `response_time` 평균은 읽기 전용 공개 대시보드 API(`/api/dashboard/v3/analysis`)에서 조회했다. Nginx Proxy Manager access/error 로그, FastAPI 운영 access/error 로그, Cloudflare 감사 로그는 제공된 자료에서 확인되지 않았다.
- 집계 방법: JSON 형식 Airflow 로그의 타임스탬프, `Generated ... elapsed=...s`, 각 항목의 `done (...s)`, `error_detail`을 파싱했다. 성공한 시도만 완료시간 비교에 넣었다. 여러 실행이 있으면 실행시간 중앙값을 사용했다. P50/P95/P99는 관측치를 정렬한 뒤 올림 순위 값을 사용했다.
- **측정 범위:** `elapsed`는 생성 함수 전체 시간으로, Airflow 큐 대기시간은 제외된다. 항목별 `done (...s)`는 API 호출에 JSON 파일 쓰기와 해당 루프 처리까지 포함한다. 이것은 **순수 HTTP 응답시간이 아니다.** FastAPI 처리시간, DNS·TLS·연결 설정시간도 따로 분리할 수 없다.
- 로그만으로 DAG run 자체의 시작·종료 상태 메타데이터를 완전히 복원할 수 없어, 이 보고서의 실행시간은 해당 생성 **Task의 함수 실행시간**이다.

## 3. Cloudflare 설정 변경

사용자가 설명한 구성은 전환 전 `Airflow/사용자 → Cloudflare Proxy → Nginx Proxy Manager → FastAPI`, 전환 후 `Airflow/사용자 → DNS Only → Nginx Proxy Manager → FastAPI`이다. Airflow static DAG 13개는 실제로 `https://back.eftlibrary.com/api`를 사용한다. 가격 static DAG는 같은 URL 상수를 정의하지만 생성 경로에서는 DB를 직접 읽으며 HTTP API를 호출하지 않는다.

사용자가 확인한 DNS Only 전환 시각은 **2026-09-27 22:00 KST**다. 과거 DNS 설정 화면·Cloudflare 감사 로그·DNS 응답 이력은 제공되지 않아 이 시각은 독립 검증되지 않았다. 로그에는 **전환 전인 9월 27일 새벽의 느린 실행과 전환 후인 9월 28일 새벽의 빠른 실행**이 관측된다. 이 시간적 선후관계만으로 원인을 특정할 수는 없다. [Cloudflare의 Proxy 상태 문서](https://developers.cloudflare.com/dns/proxy-status/)에 따르면 DNS Only는 HTTP 요청을 Cloudflare 프록시로 보내지 않고 원본 주소로 연결한다. 이 문서는 경로의 차이를 설명하며, 이번 서비스의 지연 원인을 증명하지는 않는다.

분석을 혼동할 후속 변경도 있다. 백엔드 Git 이력 `b1a3474`에는 **2026-10-03 09:32 KST**에 IP별 요청 제한 기본값을 100건대에서 **1,000건/분**으로 높인 변경이 있다. Airflow Git 이력 `392cc48`에는 같은 날 **09:49 KST**에 static API 요청 사이 **1.1초 대기 및 429 재시도**가 추가됐다. Git 커밋 시각은 운영 배포 시각이 아니다. 10월 3일 실행 중 어느 코드 버전이 사용됐는지는 배포 기록이 없어서 확정하지 않았다.

## 4. Airflow 성능 분석

아래 중앙값은 성공한 **예약 실행**을 기본으로 한다. `item`은 당시 수동 실행만 있었고, `quest`의 전환 후 성공 표본도 수동 재시도 한 건뿐이다. `n`은 비교에 사용한 성공 시도 수다.

| 생성 Task (`v3_dags_…_static_json`) | Proxy 추정: 중앙값, n | DNS Only 추정: 중앙값, n | 실행시간 감소 |
|---|---:|---:|---:|
| `generate_item_static_json` | 3,289.83초, 2 | 287.45초, 1 | 91.3% |
| `generate_quest_static_json` | 322.89초, 58 | 27.58초, 1 수동 시도 | 91.5% |
| `generate_live_map_static_json` | 217.96초, 43 | 16.03초, 1 | 92.6% |
| `generate_map_static_json` | 47.95초, 58 | 2.60초, 6 | 94.6% |
| `generate_boss_static_json` | 31.08초, 58 | 2.04초, 6 | 93.4% |
| `generate_hideout_static_json` | 18.05초, 58 | 1.33초, 6 | 92.6% |
| `generate_story_static_json` | 8.82초, 58 | 0.56초, 6 | 93.7% |
| `generate_price_static_json` | 32.83초, 1,390 | 32.55초, 132 | 0.9% |

`price`는 API 호출 없이 DB 데이터를 읽는 대조군이다. 이 작업의 실행시간이 거의 그대로인 점은 전체 Airflow나 서버가 일률적으로 10배 빨라진 설명과 맞지 않는다. 다만 DB 작업량 및 다른 배포 변경을 통제한 실험은 아니다.

대표 실행 기록은 다음과 같다. 시각은 모두 KST이며, 시작·종료는 로그 첫/마지막 이벤트다. 함수의 `elapsed`와 수십 밀리초 차이가 날 수 있다.

| DAG / Task | 구간 | 시작 | 종료 | `elapsed` | 성공한 항목 수 |
|---|---|---|---|---:|---:|
| item / `generate_item_static_json` | Proxy 추정 | 09-14 07:40:04 | 09-14 08:35:21 | 3,317.48초 | 5,532 item + 16 list |
| item / `generate_item_static_json` | DNS Only 추정 | 10-03 09:36:31 | 10-03 09:41:19 | 287.45초 | 5,655 item + 16 list |
| quest / `generate_quest_static_json` | Proxy 추정 | 09-27 05:15경 | 09-27 05:20경 | 315.79초 | 484 quest + 17 trader + 3 고정 API |
| quest / `generate_quest_static_json` | DNS Only 추정 | 10-03 09:27:40경 | 10-03 09:28:08경 | 27.58초 | 485 quest + 17 trader + 3 고정 API |

아이템 기록: [9월 14일 로그](logs/dag_id=v3_dags_item_static_json/run_id=manual__2026-09-13T22:40:02+00:00/task_id=generate_item_static_json/attempt=1.log), [10월 3일 로그](logs/dag_id=v3_dags_item_static_json/run_id=manual__2026-10-03T00:36:29+00:00/task_id=generate_item_static_json/attempt=1.log). 다른 DAG의 집계도 같은 `logs/dag_id=.../run_id=.../task_id=.../attempt=*.log`에서 계산했다.

항목별 처리시간은 직접적인 HTTP 응답시간은 아니지만, API 호출이 지배적인 반복 루프의 변화를 보여준다.

| 항목별 처리시간 | Proxy 추정 | DNS Only 추정 |
|---|---:|---:|
| item: 관측 항목 수 | 11,085 | 5,671 |
| item: 평균 / 최소 / 최대 | 0.594 / 0.55 / 2.74초 | 0.051 / 0.04 / 0.15초 |
| item: P50 / P95 / P99 | 0.59 / 0.63 / 0.74초 | 0.05 / 0.06 / 0.06초 |
| quest: 관측 항목 수 | 29,466 (전환 전 예약 성공 실행) | 502 (전환 후 수동 성공 실행) |
| quest: 평균 / 최소 / 최대 | 0.647 / 0.46 / 13.39초 | 0.054 / 0.04 / 0.79초 |
| quest: P50 / P95 / P99 | 0.59 / 0.87 / 1.62초 | 0.05 / 0.05 / 0.35초 |

성공 시도의 요청 수는 생성 항목 수와 고정 API 호출 수로 계산할 수 있다. 예를 들어 item 9월 14일은 **5,548건**, 10월 3일은 **5,671건**이다. 실패 시도는 첫 실패 지점 이후 호출이 없고, 응답 실패에 `done` 로그가 남지 않으므로 정확한 HTTP 요청 총수는 확인 불가다.

Airflow static 로그의 실패 `error_detail`에서 전환 전 **HTTP 429 오류 6회**, 전환 후 **14회**가 관측됐다. 이는 HTTP 트래픽 전체가 아닌 **Task가 실패하며 기록한 429 횟수**다. 전환 전에는 연결 오류 한 시도에서 `ConnectionError → ProtocolError → ConnectionResetError` 원인 사슬이 있었다. 여러 예외 이름은 한 실패에 속하므로 세 번으로 세지 않았다. 명시적인 timeout 예외는 이 static 로그에서 관측되지 않았다. 재시도 파일(`attempt>1`)은 구간별 **9개**였다. 실패 후 자동 재시도인지 수동 재실행인지 DAG run ID와 attempt로 구분 가능한 범위만 집계했으며, Airflow 전체 재시도 총량으로 확대하지 않는다. 10월 3일 예약 item 실행은 09:53:52 KST에 대상을 읽고, 항목 처리시간이 대체로 1.10초인 상태에서 580번째 item 처리 중 10:04:46 KST에 **`Task killed!`**가 기록됐다. 성공 실행이 아니므로 성능 비교에서 제외했다. 로그에는 kill 원인이 없으므로 메모리 부족·타임아웃 등으로 단정하지 않는다.

특히 퀘스트 예약 DAG는 9월 28일부터 10월 3일까지 429로 중단된 시도가 많다. 실패한 10초대 시도를 성공한 300초대 시도와 비교해 성능 개선으로 계산해서는 안 된다.

## 5. FastAPI 성능 분석

FastAPI 소스 `main.py`는 `uvicorn.access` 로그를 끄고, `util/middleware.py`의 `api.access` 로그에서 경로, 응답 코드, `process_time`을 기록한다. 제공된 `logs/`에는 이 FastAPI 운영 access/error 로그가 없다. 따라서 **요청 수, endpoint별 요청 수·평균·P95·P99, 가장 느린 API Top 10, HTTP 4xx/5xx 총량, 특정 시간대의 서버 처리 지연은 확인 불가**다.

백엔드 코드상 IP별 1분 요청 제한이 있으며, 10월 3일 커밋 전 조건은 `len(request_counts[ip]) > 100`이었다. 최근 커밋에서는 기본값 `API_RATE_LIMIT_PER_MINUTE=1000`을 사용한다. Airflow의 429는 백엔드 제한과 부합하지만, 개별 429가 반드시 이 미들웨어에서 발생했는지 입증할 서버 로그는 없다. 사용자 IP는 `CF-Connecting-IP`, `X-Real-IP`, `X-Forwarded-For`, 연결 주소 순으로 선택된다. DNS Only에서 Cloudflare 헤더가 사라질 수 있으므로 실제 집계 IP는 Nginx 설정과 운영 로그로 확인해야 한다.

### `response_time` 테이블의 외부 헬스체크 지표

Airflow `dags_health_check`는 5분마다 `https://back.eftlibrary.com/health`와 `https://eftlibrary.com/health`를 `requests.get(timeout=10)`으로 호출한다. 측정값을 `response_time(service_name, response_ms, checked_time)`에 넣는다. **`response_ms`라는 열 이름과 달리 실제 저장값은 `time.time()` 차이인 초 단위**다. 대시보드 API는 평균에 1,000을 곱해 밀리초로 반환한다. 이 값은 Airflow에서 본 외부 HTTPS 헬스체크의 전체 소요시간이며 FastAPI/Next.js 내부 처리시간이나 일반 업무 API 평균이 아니다. 요청 중 예외가 나면 `NULL`이 들어가고 API 평균 계산에서 제외된다. 코드상 비정상 HTTP status만으로는 측정값이 제외되지 않는다.

전환일 9월 27일을 통째로 제외한 동일 길이 5일 구간을 비교했다. 기간 경계는 대시보드 API가 `checked_time AT TIME ZONE 'Asia/Seoul'`에 적용하는 값이다. 아래 수치는 API가 반환한 **반올림된 평균**이므로 원본 분포·표본 수는 알 수 없다. 표의 기간은 실제 측정 시각이 아니라 DB에 저장된 `checked_time` 필터 구간이다.

| 서비스 / 외부 헬스체크 | 전환 전: 저장 시각 09-22 00:00~09-27 00:00 | 전환 후: 저장 시각 09-28 00:00~10-03 00:00 | 평균 감소 |
|---|---:|---:|---:|
| FastAPI `back.eftlibrary.com/health` | 1,020ms | 43ms | 95.8% |
| Next.js `eftlibrary.com/health` | 3,339ms | 300ms | 91.0% |

조회는 각각 `/api/dashboard/v3/analysis?start_date=2026-09-22T00%3A00%3A00&end_date=2026-09-27T00%3A00%3A00`와 `/api/dashboard/v3/analysis?start_date=2026-09-28T00%3A00%3A00&end_date=2026-10-03T00%3A00%3A00`에서 수행했다. 직접 DB에 접속하지 않았으며 API는 `COUNT`, 최소/최대, P50/P95/P99 또는 개별 측정값을 제공하지 않는다. 따라서 이 항목들은 **확인 불가**다.

**시각 해석 주의:** Airflow 코드는 `checked_time`에 시간대 없는 `datetime.now()`를 넣었다. 10월 4일 **08:50 KST**의 `measure_response_time` 태스크가 성공했는데 DB에 보이는 마지막 행은 **10월 3일 23:50 KST**였다. 정확히 9시간 차이여서 컨테이너와 DB의 시간대 해석이 어긋난 것으로 판단된다. 9월 27일 **20~22시로 필터링한 기록이 이미 FastAPI 평균 44ms, Next.js 298ms**인 것도 이 시각 오차와 부합한다. DB 세션 시간대 자체는 직접 확인하지 못했다. 따라서 과거 `checked_time`을 정확한 실제 측정 시각으로 사용하지 않으며, 전환일을 비교에서 제외했다. 적재 방식과 기존 기록은 변경하지 않았다.

## 6. Nginx Proxy Manager 분석

Nginx Proxy Manager의 access/error 로그와 운영 설정 파일은 제공되지 않았다. 따라서 `request_time`, `upstream_response_time`, 두 값의 차이, 499/502/503/504, upstream 연결 실패·reset·timeout, 동일 요청 반복은 **확인 불가**다. NPM 헬스체크 스크립트에서 내부 호스트 NPM 관리 엔드포인트와 FastAPI의 내부 주소 사용 흔적은 확인되지만, 이것은 프록시 성능 로그가 아니다.

향후 동일 요청의 Nginx `request_time - upstream_response_time`이 Proxy 구간에서만 크게 나타나면 원본 API 처리 외 구간의 지연을 의심할 수 있다. 단, Nginx는 Cloudflare와 원본 서버 사이에 위치하므로 **Cloudflare 앞쪽 구간의 시간을 Nginx `request_time`만으로 모두 볼 수는 없다.** Airflow 클라이언트의 전체 요청시간과 함께 비교해야 한다.

## 7. 전환 전후 비교

아래는 증거 수준을 분명히 하기 위한 요약이다. `item`은 서로 다른 날짜의 수동 실행 2건 대 1건, `quest`는 전환 후 성공 표본 1건이다.

| 지표 | Proxy 추정 | DNS Only 추정 | 변화 |
|---|---:|---:|---:|
| item 함수 실행시간 중앙값 | 3,289.83초, n=2 | 287.45초, n=1 | 91.3% 감소 |
| quest 함수 실행시간 중앙값 | 322.89초, n=58 | 27.58초, n=1 | 91.5% 감소, 표본 적음 |
| item 항목 처리시간 평균 | 0.594초 | 0.051초 | 91.4% 감소 |
| item 항목 처리시간 P95 / P99 | 0.63 / 0.74초 | 0.06 / 0.06초 | 각각 90.5% / 91.9% 감소 |
| 외부 FastAPI 헬스체크 평균 (`response_time`) | 1,020ms | 43ms | 95.8% 감소 |
| 외부 Next.js 헬스체크 평균 (`response_time`) | 3,339ms | 300ms | 91.0% 감소 |
| 헬스체크 P50 / P95 / P99, 표본 수 | 확인 불가 | 확인 불가 | 확인 불가 |
| 일반 API의 순수 HTTP 응답시간 평균 / P95 / P99 | 확인 불가 | 확인 불가 | 확인 불가 |
| FastAPI endpoint별 처리시간 | 확인 불가 | 확인 불가 | 확인 불가 |
| Nginx request/upstream time | 확인 불가 | 확인 불가 | 확인 불가 |
| static Task 실패에 기록된 HTTP 429 | 6회 | 14회 | 전환 후 증가; 노출 기간·시도 수 다름 |
| static Task 실패에 기록된 timeout | 0회 관측 | 0회 관측 | 미계측 요청 내부의 timeout 부재까지 증명하지 않음 |
| static 재시도 파일 `attempt>1` | 9개 | 9개 | 분모가 달라 직접 비교 곤란 |

## 8. 원인 분석

**확인된 사실:** 여러 API 호출 static DAG의 처리시간이 9월 28일경부터 대략 한 자릿수~십수 배 빨라졌다. `response_time`의 외부 헬스체크 평균도 전후 5일 비교에서 FastAPI 1,020→43ms, Next.js 3,339→300ms로 낮아졌다. API를 호출하지 않는 가격 static DAG는 거의 변하지 않았다. 빠른 구간에는 429가 더 자주 노출됐다. Cloudflare 변경 시각은 사용자 제공 정보이며, 서버·프록시 내부 타이밍은 확인되지 않았다.

| 가설 | 평가 | 근거와 한계 |
|---|---|---|
| A. FastAPI 자체가 느렸다 | 근거 부족 | FastAPI `process_time` 운영 로그가 없어 서버 처리시간의 전후 변화는 모른다. DB·캐시 상태도 통제되지 않았다. |
| B. Cloudflare Proxy 경로가 지연을 유발했다 | 가능성이 높음 | DNS Only 전환 설명과 다수 DAG의 동시 급변, DB 직접 작업의 안정성은 일치한다. Cloudflare·Nginx 구간별 시간은 없다. |
| C. Cloudflare 경로의 timeout/retry가 주원인이었다 | 근거 부족 | static 로그에는 전환 전 연결 reset 1시도가 있으나 대량 timeout·재시도 증거는 없다. 1시간 작업의 5천여 항목이 각각 약 0.6초인 양상은 *반복적인 일정 지연*과도 맞는다. |
| D. DNS/TLS/연결 설정 비용이 반복됐다 | 가능성이 있음 | 기존 코드는 각 호출에 `requests.get`을 직접 사용하고 `Session` 재사용이 없다. 매 요청의 DNS/TCP/TLS 소요시간은 계측되지 않아 기여도를 계산할 수 없다. DNS Only 후에도 HTTPS 연결 자체는 여전히 있다. |
| E. 같은 서버의 FastAPI를 공인 도메인으로 돌아서 호출했다 | 코드로 확인됨, 배치 위치는 미확인 | 13개 static DAG가 `https://back.eftlibrary.com/api`를 사용한다. 헬스체크는 내부 비공개 내부 주소로 FastAPI에 접근한다. Airflow와 FastAPI가 실제로 같은 호스트/네트워크에 배치됐는지는 운영 배치 정보가 필요하다. |

일반적으로 Cloudflare 프록시를 제거하면 홉이 줄지만, 이는 항상 웹사이트가 빨라진다는 뜻이 아니다. 이번 **약 90% 단축**은 홉 하나의 통상적인 비용만으로 단정해 설명하기 어렵다. 반복 연결 설정, 원본 연결 상태, 프록시 동작, 캐시·DB 상태 또는 다른 배포 변경이 합쳐졌을 수 있다. 어느 요인이 지배적이었는지는 계층별 시간과 동일 조건의 재현 실험이 필요하다.

별도 병목/운영 영향도 확인됐다. static 호출은 `requests.Session` 없이 요청마다 연결을 만들고, 백엔드 제한은 IP별 전체 API 요청을 합산한다. 빠른 경로에서 퀘스트 DAG가 429로 중단되어, **짧은 실패시간이 실제 산출물 생성 성공을 의미하지 않는다.** 현재 저장소의 1.1초 요청 간격은 5,671건의 요청에 **최소 약 104분**의 간격 대기/간격 시간을 만든다(요청 자체의 응답시간 및 파일 쓰기 제외). 10월 3일 오전 9시 36분의 4분 47초 **성공 로그는 이 대기가 적용된 실행이 아니었음이 항목별 약 0.05초 기록으로 드러난다.** 반면 09:53 이후 예약 실행은 항목별 약 1.10초였고 중간에 종료됐다. 해당 throttle은 새 성능 병목이며, 실제 배포된 백엔드 1,000건/분 제한과 다른 트래픽을 확인한 뒤 간격을 재조정할 필요가 있다.

## 9. 추가 개선 권장사항

### High

1. **같은 네트워크 안에서 Airflow → FastAPI 직접 호출 검증:** 우선 현재 컨테이너에서 내부 호스트(예: 내부 FastAPI 주소 또는 Docker 서비스명)로 같은 endpoint에 접근되는지 읽기 전용으로 확인한다. `localhost` 주소는 두 서비스가 **같은 네트워크 네임스페이스**에 있을 때만 유효하다. 내부 전환은 Cloudflare·공인 DNS·외부 TLS 경로를 피하고 429의 IP 집계 경로도 단순화할 수 있다. 반면 내부 인증·TLS 요구사항, 서비스 발견, 네트워크 분리, 응답 캐시 경로 차이를 점검해야 한다. **이번 분석에서는 코드를 변경하지 않았다.**
2. **429 이후의 정상 완료 검증 및 throttle 재평가:** 제한 상향·대기 코드가 실제 운영에 배포된 시각을 확인하고, 퀘스트·live-map·item DAG의 다음 *성공 실행*을 점검한다. 특히 item 예약 실행의 `Task killed!` 원인과 1.1초 간격이 만드는 100분 이상 처리시간을 검토한다. 실패 뒤 재시도 횟수와 생성 파일 수를 함께 본다.
3. **Cloudflare 변경 시각 검증:** 사용자 제공 시각(2026-09-27 22:00 KST)을 DNS 레코드 감사 기록 또는 변경 기록과 대조하고, 전후 동일 시각대·동일 DAG 버전의 로그만 다시 비교한다.

### Medium

1. Airflow에서 요청별 총시간, 상태 코드, 재시도, 가능하면 DNS/연결/TLS 시간을 수집한다. URL에 사용자 데이터가 있으면 집계 시 마스킹한다.
2. NPM access 로그에 `request_time`, `upstream_response_time`, `upstream_connect_time`, status를 기록하고 FastAPI `process_time`과 동일 요청 ID로 연결한다. 원본 API 로그의 개인정보와 IP는 분석 시 가린다.
3. 내부 통신 전환 전후 동일 endpoint·동일 호출량의 실험을 별도 시간대에 반복하고, `requests.Session`을 이용한 연결 재사용 효과도 별도로 측정한다.

### Low

1. DAG별 성공 실행시간, 완료 항목 수, 429/5xx/timeout 수의 장기 추세를 보존한다.
2. static 생성 작업과 DB 직접 생성 작업을 구분한 대시보드를 만든다.

## 10. 결론

제공된 로그는 **아이템 static 55분대 → 4분 47초, 약 91.3% 단축**과 여러 API 호출 DAG의 동시적인 속도 개선을 뒷받침한다. `response_time` 헬스체크 평균도 FastAPI **95.8%**, Next.js **91.0%** 감소했다. 이 현상은 Cloudflare Proxy 경로를 제거한 변화와 시간상 부합하며, 특히 API 호출 작업만 크게 변한 점이 중요하다. 그러나 사용자 제공 변경 시각을 독립 검증할 감사 기록, FastAPI 서버 처리시간, Nginx upstream 시간, 클라이언트 연결 단계 시간이 없어 **병목 지점을 특정하거나 인과관계를 확정할 수 없다.** 다음 단계는 운영 로그와 변경 이력을 확보하고, 내부 API 경로를 동일 조건에서 비교하는 것이다.
