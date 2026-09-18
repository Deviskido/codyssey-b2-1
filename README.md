# 용돈 기입장

Python 3.10 이상과 표준 라이브러리만 사용하는 콘솔 가계부입니다. 별도 `pip install`은 필요하지 않습니다. [요구사항](requirements.txt)과 [완료된 구현 칸반](KANBAN.md)을 참고하세요.

## 실행

프로젝트 루트에서 실행합니다. 이 환경의 `python3`는 3.9이므로 아래 예시는 설치된 `python3.12`를 사용합니다. 다른 환경에서는 Python 3.10 이상을 가리키는 `python` 또는 `python3`로 바꿔도 됩니다.

```sh
python3.12 -m budget_app --help
python3.12 -m budget_app add
python3.12 -m budget_app list --limit 10
python3.12 -m budget_app --data-dir ./my-ledger list
```

모든 명령 및 하위 명령은 `--help`를 지원합니다. 옵션은 `--`로 통일합니다. `--data-dir`는 최상위 명령 앞 또는 바로 뒤에 지정합니다. 예: `--data-dir ./my-ledger budget set ...` 또는 `budget --data-dir ./my-ledger set ...`.

`add`는 날짜, 타입, 카테고리, 양수 정수 금액, 메모, 태그를 순서대로 묻고 저장된 ID를 출력합니다. 선택 값은 Enter로 생략합니다. 잘못된 입력은 원인과 힌트를 출력하고 비0 코드로 종료하므로 값을 확인하여 다시 실행하세요. 정상 종료 코드는 0입니다. 일부 CSV 행을 건너뛴 경우에도 비0 코드를 반환합니다.

## 명령 예시

```sh
# 카테고리 추가/삭제는 이름을 대화형으로 입력
python3.12 -m budget_app category add
python3.12 -m budget_app category list
python3.12 -m budget_app category remove

# 기간의 양 끝 날짜를 포함하며, 조건은 AND로 결합
python3.12 -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food --type expense --q 점심 --tag meal

# update는 옵션 방식으로 고정. TX-ID는 실제 ID로 교체
python3.12 -m budget_app update --id TX-ID --date 2024-01-16 --amount 12000 --memo 점심 --tags meal,work
python3.12 -m budget_app update --id TX-ID --memo "" --tags ""
python3.12 -m budget_app delete --id TX-ID

python3.12 -m budget_app budget set --month 2024-01 --amount 500000
python3.12 -m budget_app summary --month 2024-01 --top 3

python3.12 -m budget_app export --out january.csv --month 2024-01
python3.12 -m budget_app export --out period.csv --from 2024-01-01 --to 2024-02-29
python3.12 -m budget_app import --from january.csv

python3.12 -m budget_app backup
python3.12 -m budget_app recurring add
python3.12 -m budget_app recurring list
python3.12 -m budget_app recurring generate --month 2024-02
```

- `list` 기본 제한은 20건입니다. 최신순은 거래 날짜 내림차순이며, 같은 날짜는 저장 순서의 역순입니다. 수정은 기존 저장 순서를 유지합니다.
- 검색의 `--q`는 대소문자를 구분하는 메모 부분 문자열, `--tag`는 태그 하나와의 정확한 일치입니다. 조건이 없는 검색은 전체 거래를 출력합니다.
- `update`는 지정한 필드만 변경하고 ID를 유지합니다. 변경 가능한 필드는 `date/type/category/amount/memo/tags`이며 하나 이상 지정해야 합니다. 없는 ID의 수정/삭제는 오류입니다.
- `summary` 기본 TOP 개수는 3입니다. 총수입/총지출/잔액과 지출 순위를 표시합니다. 예산 조회는 이 명령에서 이루어지며 사용률은 지출 ÷ 예산 × 100입니다. 예산보다 지출이 클 때 경고합니다. 빈 월은 `데이터 없음`을 표시합니다.
- 사용 중인 카테고리(거래 또는 반복 규칙에서 참조)는 삭제할 수 없습니다. 중복/빈 이름은 거부합니다.
- 표에서 카테고리는 16칸, 메모는 30칸으로 잘라 표시합니다. 저장값은 유지하며 CSV로 전체 내용을 확인할 수 있습니다. 한글의 표시 너비를 고려합니다.

## 저장 파일

기본 경로는 **현재 작업 디렉터리의 `./data`**입니다. 초기 실행 시 폴더와 파일을 생성합니다. 빈 카테고리 파일에는 `food`, `transport`, `rent`, `salary`, `etc`를 자동 등록합니다.

| 파일 | UTF-8 JSONL 레코드 |
| --- | --- |
| `transactions.jsonl` | `id`, `type`, `date`, `amount`, `category`, `memo`, `tags` |
| `categories.jsonl` | `name` |
| `budgets.jsonl` | `month`, `amount` |
| `recurring.jsonl` | 거래 템플릿 필드와 규칙 `name`, `day` |

JSONL은 한 줄에 JSON 객체 하나를 저장합니다. `amount`는 양수 정수, `tags`는 문자열 배열입니다. 거래 ID는 UUID 기반입니다. 예:

```json
{"id":"TX-example","type":"expense","date":"2024-01-15","amount":15000,"category":"food","memo":"점심","tags":["meal"]}
```

파일 변경은 같은 폴더의 임시 파일에 기록하고 flush/fsync 후 `os.replace`로 교체합니다. 수정/삭제 대상이 없거나 쓰기가 실패하면 기존 파일을 유지합니다. 거래 추가와 import도 같은 정책을 사용하므로 기존 파일 크기에 비례하는 재작성 비용이 있습니다. 동시에 여러 프로세스에서 같은 저장 폴더에 쓰는 사용 방식은 지원하지 않습니다.

## CSV 계약

UTF-8, 헤더 포함. export 열 순서는 아래와 같습니다. import는 필수 열을 모두 요구하며 `memo`, `tags`가 없는 파일도 허용합니다. ID는 CSV에 포함하지 않고 가져올 때 새로 생성합니다.

| 열 | 필수 | 형식 |
| --- | --- | --- |
| `date` | 예 | 유효한 `YYYY-MM-DD` |
| `type` | 예 | `income` 또는 `expense` |
| `category` | 예 | 이미 등록된 카테고리 |
| `amount` | 예 | 양수 정수 |
| `memo` | 아니요 | 문자열 |
| `tags` | 아니요 | 쉼표로 구분한 태그 문자열 |

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,"점심, 커피","meal,work"
2024-01-16,income,salary,3000000,월급,
```

쉼표/줄바꿈/따옴표를 포함한 필드는 CSV 인용 규칙을 따릅니다. 표준 `csv` 모듈이 인용과 이스케이프를 처리합니다. tags는 쉼표를 구분자로 사용하므로 태그 자체에는 쉼표를 넣지 않습니다.

import는 잘못된 행을 건너뛰고 행 번호, 원인, 해결 힌트를 출력하며 `imported`/`skipped`를 보고합니다. 필수 헤더 누락 또는 파일 읽기/쓰기 실패 시 거래 파일을 교체하지 않습니다. 같은 CSV를 다시 가져오면 새 거래로 추가됩니다. 실패한 행만 수정해 별도 파일로 가져오세요.

export는 `--month` 또는 `--from`/`--to`가 필수이며 월과 기간 조건을 함께 지정할 수 없습니다. 기간은 한쪽 경계만 지정해도 됩니다. 결과가 없으면 헤더만 생성합니다. 결과 건수를 출력하며 기존 출력 CSV는 성공 시 교체합니다. 앱 저장 파일 경로로의 내보내기는 차단합니다.

## 백업과 반복 내역

`backup`은 저장 폴더에 `backup-YYYYMMDD-HHMMSS-ffffff.zip`을 만들고 JSONL 파일 4개를 포함합니다. 복구하려면 앱 실행을 중단하고 기존 데이터를 별도로 보관한 다음 ZIP의 파일들을 저장 폴더에 풀어 덮어씁니다. 예를 들어 새로운 폴더로 복원하여 먼저 확인할 수 있습니다.

```sh
python3.12 -m zipfile -e data/backup-실제타임스탬프.zip restored-data
python3.12 -m budget_app --data-dir restored-data list
```

`recurring add`는 고유한 규칙명, 매월 날짜(1~31), 타입/카테고리/금액/메모/태그를 묻습니다. 월에 해당 일이 없으면 말일로 조정합니다. 예를 들어 31일 규칙은 2024년 2월에 29일 거래를 만듭니다. 규칙 ID와 대상 월로 생성 ID를 정하여 같은 월 재실행 시 기존 거래를 중복 생성하지 않습니다. 생성 거래를 삭제하면 해당 월 재실행으로 다시 생성할 수 있습니다. 규칙 수정/삭제 CLI는 제공하지 않습니다.

## 구조와 검증

- `models.py`: `Transaction` dataclass, 날짜/월/금액 검증, 명시적 타입 힌트. 예를 들어 `positive(value) -> int`는 검증된 양수 정수를 반환합니다.
- `storage.py`: `JsonStore`, `TransactionRepository`. `records()`는 `yield`로 한 줄씩 읽고 파일 변경은 원자적 교체로 수행합니다.
- `service.py`: CRUD, 검색, 집계, 예산, CSV, 백업, 반복 거래의 업무 규칙입니다.
- `cli.py`: argparse, 대화형 입력, 한글 너비를 고려한 출력, 실제 적용된 `handle_errors` 데코레이터입니다. 데코레이터가 예외 메시지와 종료 코드를 명령 로직에서 분리합니다.
- `__main__.py`: 모듈 실행 진입점입니다.

목록/검색/내보내기는 파일 전체를 Python 리스트에 적재하지 않습니다. 제너레이터에서 필터링한 거래를 임시 디스크 SQLite로 흘려 보내고 날짜/저장 순서로 정렬한 커서를 순회합니다. SQLite는 표준 라이브러리의 일시적인 정렬 작업 공간이며 영구 저장 형식은 JSONL입니다. SQLite 페이지 캐시는 1 MiB로 설정하고 임시 정렬은 파일을 사용합니다. 출력 전에 전체 입력을 스캔해야 하며 임시 디스크 공간이 필요합니다. 요약은 한 번 순회하면서 합산합니다.

```sh
python3.12 -m unittest discover -s tests -v
```

테스트는 임시 폴더를 사용합니다. CRUD와 재실행 영속성, 최신순/limit, 복합 검색, 요약/예산, 카테고리 보호, CSV 왕복/실패 정책, 대화형 CLI, 모든 help, 오류 종료, 손상 파일, 원자적 교체 실패, 백업, 반복 거래 중복 방지, 한글 정렬을 확인합니다. 12,000건 정렬 테스트는 Python 메모리 최고 사용량을 4 MiB 미만으로 검증합니다(`tracemalloc`은 SQLite의 네이티브 메모리를 포함하지 않습니다).
