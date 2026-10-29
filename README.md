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

# 선택 기능인 backup, recurring 명령은 현재 비활성화되어 있습니다.
```

- `list` 기본 제한은 20건입니다. 최신순은 거래 날짜 내림차순이며, 같은 날짜는 저장 순서의 역순입니다. 수정은 기존 저장 순서를 유지합니다.
- 검색의 `--q`는 대소문자를 구분하는 메모 부분 문자열, `--tag`는 태그 하나와의 정확한 일치입니다. 조건이 없는 검색은 전체 거래를 출력합니다.
- `update`는 지정한 필드만 변경하고 ID를 유지합니다. 변경 가능한 필드는 `date/type/category/amount/memo/tags`이며 하나 이상 지정해야 합니다. 없는 ID의 수정/삭제는 오류입니다.
- `summary` 기본 TOP 개수는 3입니다. 총수입/총지출/잔액과 지출 순위를 표시합니다. 예산 조회는 이 명령에서 이루어지며 사용률은 지출 ÷ 예산 × 100입니다. 예산보다 지출이 클 때 경고합니다. 빈 월은 `데이터 없음`을 표시합니다.
- 사용 중인 카테고리(거래 또는 반복 규칙에서 참조)는 삭제할 수 없습니다. 중복/빈 이름은 거부합니다.
- 거래는 `|` 구분자로 출력합니다. 선택 기능인 고정 너비 표 정렬과 문자열 잘라내기는 비활성화했습니다.

## 파서·서브파서·아규먼트 트리

`python3.12 -m budget_app list --limit 3`에서 `list`는 수행할 **명령(command)**, `--limit`는 **옵션(option)**, `3`은 옵션의 값입니다. 이처럼 프로그램에 전달하는 입력을 넓게 **인자(argument)**라고 합니다.

| 코드 | 역할 |
| --- | --- |
| `Parser()` | 프로그램 전체의 입력 규칙을 담는 최상위 파서 생성 |
| `add_subparsers()` | 여러 하위 명령 중 하나를 선택하는 구조 생성 |
| `add_parser("list")` | `list`라는 하위 명령과 그 명령의 파서 생성 |
| `add_argument("--limit")` | 해당 파서가 받을 옵션과 값의 규칙 등록 |

아래는 `budget_app/cli.py`의 현재 활성화된 전체 구조입니다. `[파서]`는 입력 규칙을 담는 객체이고, `[명령 선택]`은 `add_subparsers()`로 생성한 구조입니다. 모든 파서에 자동으로 추가되는 `-h / --help`는 반복을 줄이기 위해 트리에서 생략했습니다.

```text
root [최상위 파서: Parser()]
│
├── --data-dir → args.data_dir
│   └── 기본값: "./data"
│
└── commands [명령 선택: dest="command", required=True]
    │
    ├── add [파서] → args.command = "add"
    │   └── --data-dir
    │
    ├── list [파서] → args.command = "list"
    │   ├── --data-dir
    │   └── --limit → args.limit
    │       └── 양수 정수, 기본값: 20
    │
    ├── search [파서] → args.command = "search"
    │   ├── --data-dir
    │   ├── --from     → args.start
    │   ├── --to       → args.end
    │   ├── --category → args.category
    │   ├── --type     → args.type
    │   │   └── income 또는 expense
    │   ├── --q        → args.q
    │   └── --tag      → args.tag
    │
    ├── update [파서] → args.command = "update"
    │   ├── --data-dir
    │   ├── --id       → args.id        [필수]
    │   ├── --date     → args.date
    │   ├── --type     → args.type
    │   ├── --category → args.category
    │   ├── --amount   → args.amount
    │   ├── --memo     → args.memo
    │   └── --tags     → args.tags
    │
    ├── delete [파서] → args.command = "delete"
    │   ├── --data-dir
    │   └── --id → args.id              [필수]
    │
    ├── summary [파서] → args.command = "summary"
    │   ├── --data-dir
    │   ├── --month → args.month        [필수]
    │   └── --top   → args.top
    │       └── 양수 정수, 기본값: 3
    │
    ├── budget [파서] → args.command = "budget"
    │   ├── --data-dir
    │   └── sub [명령 선택: dest="action", required=True]
    │       └── set [파서] → args.action = "set"
    │           ├── --month  → args.month   [필수]
    │           └── --amount → args.amount  [필수・양수 정수]
    │
    ├── category [파서] → args.command = "category"
    │   ├── --data-dir
    │   └── sub [명령 선택: dest="action", required=True]
    │       ├── add    [파서] → args.action = "add"
    │       ├── list   [파서] → args.action = "list"
    │       └── remove [파서] → args.action = "remove"
    │
    ├── import [파서] → args.command = "import"
    │   ├── --data-dir
    │   └── --from → args.source        [필수]
    │
    └── export [파서] → args.command = "export"
        ├── --data-dir
        ├── --out   → args.out          [필수]
        ├── --month → args.month
        ├── --from  → args.start
        └── --to    → args.end
```

각 하위 명령의 `--data-dir`도 `args.data_dir`에 저장됩니다. 기본값은 `argparse.SUPPRESS`이므로 생략하면 최상위 파서에서 설정한 값을 덮어쓰지 않습니다. `budget set`의 `set`이나 `category add/list/remove`에는 이 옵션을 별도로 등록하지 않았으므로 `--data-dir`는 `budget`/`category` 앞이나 바로 뒤에 지정합니다.

일반 옵션은 별도 기본값이 없으면 생략 시 `None`이 됩니다. `dest`는 결과 속성 이름을 지정합니다. 따라서 `search --from`은 `args.start`, `import --from`은 `args.source`에 값을 저장합니다. 트리의 `[필수]`는 파서가 검사하는 필수 옵션입니다. `update`의 변경 필드 하나 이상 지정과 `export`의 월 또는 기간 지정은 파싱 후 실행 코드에서 추가로 검사합니다.

### 입력이 args에 저장되는 과정

다음 명령은 트리에서 **root → budget → set** 경로로 분석됩니다.

```sh
python3.12 -m budget_app --data-dir ./sample budget set --month 2026-10 --amount 50000
```

`parse_args()`의 결과는 선택한 경로의 값을 하나에 모은 `Namespace` 객체입니다.

```python
Namespace(
    data_dir='./sample',
    command='budget',
    action='set',
    month='2026-10',
    amount=50000
)
```

객체의 속성은 점으로 읽습니다. 딕셔너리로 보고 싶다면 `vars(args)`를 사용합니다.

```python
args.command              # "budget"
args.action               # "set"
args.amount               # 50000
vars(args)["amount"]      # 50000
```

### 대화형 입력과 파서의 구분

`add`의 날짜·금액 등은 명령줄 옵션이 아닙니다. 명령을 파싱한 뒤 `inputs()`가 질문하고 별도의 딕셔너리를 반환합니다.

```text
add 명령 파싱 완료
└── inputs() 호출 → 입력 결과 딕셔너리 반환
    ├── 날짜       → "date"
    ├── 타입       → "type"
    ├── 카테고리   → "category"
    ├── 금액       → "amount"
    ├── 메모       → "memo"
    └── 태그       → "tags"
```

`category add/remove`의 카테고리 이름도 파싱 후 `input()`으로 받습니다. `backup`과 `recurring`은 주석 처리되어 현재 파서 트리에 등록되지 않습니다.

## 저장 파일

기본 경로는 **현재 작업 디렉터리의 `./data`**입니다. 초기 실행 시 폴더와 파일을 생성합니다. 빈 카테고리 파일에는 `food`, `transport`, `rent`, `salary`, `etc`를 자동 등록합니다.

| 파일 | UTF-8 JSONL 레코드 |
| --- | --- |
| `transactions.jsonl` | `id`, `type`, `date`, `amount`, `category`, `memo`, `tags` |
| `categories.jsonl` | `name` |
| `budgets.jsonl` | `month`, `amount` |
| `recurring.jsonl` | 비활성화된 반복 규칙의 기존 데이터 보호를 위해 유지 |

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

## 선택 과제 비활성화

`requirements.txt`의 “5. 보너스 과제 (선택)”에 따라 다음 코드를 주석으로 보관합니다.

- 백업: `BudgetService.backup()`과 `backup` CLI 명령.
- 반복 내역: `BudgetService.add_rule()`, `generate()` 및 `recurring` CLI 명령.
- 출력 정렬: `cli.cell()`. 기본 거래 목록과 월별 요약 출력은 유지합니다.

원자적 교체를 수행하는 `JsonStore.replace()`는 필수 추가·수정·삭제의 공통 저장 경로이므로 유지합니다. 기존 `recurring.jsonl`은 삭제하지 않으며, 해당 규칙이 참조하는 카테고리 삭제와 파일 덮어쓰기 보호도 유지합니다. 이전 ZIP 백업은 표준 `zipfile` 모듈로 별도 폴더에 풀어 확인할 수 있습니다.

## 구조와 검증

### 콘솔 시나리오 자동 실행

macOS/Linux에서 다음 명령으로 [CONSOLE_SCENARIOS.md](CONSOLE_SCENARIOS.md)의 콘솔 시나리오 전체를 실행할 수 있습니다.

```sh
python3.12 run_console_scenarios.py
```

[run_console_scenarios.py](run_console_scenarios.py)는 문서의 `sh` 코드 블록을 순서대로 실행합니다. 대화형 질문이 나오면 문서의 입력 예시에 따라 자동으로 답하고, 실행 명령·질문·입력값·표준 출력·오류 출력을 모두 콘솔에 실시간으로 표시합니다. 거래 추가로 생성된 실제 ID는 이후 수정·삭제 명령에 자동으로 넣습니다. 문서의 셸 명령을 실제 실행하므로 이 프로젝트에서 검토한 문서를 대상으로 사용하세요.

실행마다 새로운 임시 폴더를 만들고 문서의 `./console-test` 경로를 그 폴더로 바꿉니다. 시작과 종료 시 표시되는 `transcript.log`에 전체 입출력 기록을 저장하며, 테스트 데이터와 로그는 실행 후에도 확인할 수 있도록 남깁니다. 임시 폴더는 운영체제가 나중에 정리할 수 있습니다. Python 명령은 스크립트를 실행한 인터프리터로 통일합니다.

각 명령의 실제 종료 코드를 문서의 예상 코드와 비교합니다. 오류를 의도한 단계는 예상대로 1 또는 2로 종료하면 계속 진행하고, 코드가 다르면 중단합니다. 문서 마지막의 자동 테스트도 실행합니다. 화면 내용은 실제 출력을 그대로 보여주며 예상 화면과의 자동 문자열 비교는 하지 않습니다.

명령별 제한 시간은 기본 60초입니다. 느린 환경에서는 `python3.12 run_console_scenarios.py --timeout 120`으로 늘릴 수 있고, `Ctrl+C`로 중단할 수 있습니다.

### 코드 구조와 자동 테스트

- `models.py`: `Transaction` dataclass, 날짜/월/금액 검증, 명시적 타입 힌트. 예를 들어 `positive(value) -> int`는 검증된 양수 정수를 반환합니다.
- `storage.py`: `JsonStore`, `TransactionRepository`. `records()`는 `yield`로 한 줄씩 읽고 파일 변경은 원자적 교체로 수행합니다.
- `service.py`: CRUD, 검색, 집계, 예산, CSV의 업무 규칙입니다. 백업과 반복 거래 코드는 주석으로 보관합니다.
- `cli.py`: argparse, 대화형 입력, 구분자를 사용하는 기본 출력, 실제 적용된 `handle_errors` 데코레이터입니다. 데코레이터가 예외 메시지와 종료 코드를 명령 로직에서 분리합니다.
- `__main__.py`: 모듈 실행 진입점입니다.

목록/검색/내보내기는 파일 전체를 Python 리스트에 적재하지 않습니다. 제너레이터에서 필터링한 거래를 임시 디스크 SQLite로 흘려 보내고 날짜/저장 순서로 정렬한 커서를 순회합니다. SQLite는 표준 라이브러리의 일시적인 정렬 작업 공간이며 영구 저장 형식은 JSONL입니다. SQLite 페이지 캐시는 1 MiB로 설정하고 임시 정렬은 파일을 사용합니다. 출력 전에 전체 입력을 스캔해야 하며 임시 디스크 공간이 필요합니다. 요약은 한 번 순회하면서 합산합니다.

```sh
python3.12 -m unittest discover -s tests -v
```

테스트는 임시 폴더를 사용합니다. CRUD와 재실행 영속성, 최신순/limit, 복합 검색, 요약/예산, 카테고리 보호, CSV 왕복/실패 정책, 대화형 CLI, 모든 help, 오류 종료, 손상 파일, 원자적 교체 실패를 확인합니다. 백업·반복 거래·표 정렬 테스트는 관련 코드와 함께 주석 처리했습니다. 12,000건 정렬 테스트는 Python 메모리 최고 사용량을 4 MiB 미만으로 검증합니다(`tracemalloc`은 SQLite의 네이티브 메모리를 포함하지 않습니다).
