# 용돈 기입장 콘솔 검증 시나리오

현재 구현을 기준으로 작성한 수동 검증 절차입니다. 프로젝트 루트의 macOS 터미널(zsh/bash)에서 **1번부터 순서대로** 실행합니다. 정상 처리의 종료 코드는 0이며, 오류는 원인과 힌트를 출력하고 0이 아닌 코드로 종료해야 합니다. 종료 코드는 해당 명령 **직후** `echo $?`로 확인합니다.

## 1. 검증 환경 준비 및 초기화

Python 3.10 이상이 필요합니다. 아래 환경에서는 `python3.12`를 사용합니다. 임시 폴더를 새로 만들므로 기존 `./data`는 변경하지 않습니다. 다시 검증할 때도 이 단계부터 시작하세요.

```sh
SCENARIO_DIR=$(mktemp -d /tmp/budget-scenario.XXXXXX)
ledger() { python3.12 -m budget_app --data-dir "$SCENARIO_DIR/main" "$@"; }
echo "$SCENARIO_DIR"
python3.12 -m budget_app --help
ledger add --help
ledger list
ledger category list
ls "$SCENARIO_DIR/main"
```

예상 결과:

- 도움말에 명령과 옵션이 표시됩니다.
- 목록은 헤더와 `데이터 없음`을 출력합니다.
- 기본 카테고리는 `food`, `transport`, `rent`, `salary`, `etc`입니다.
- `transactions.jsonl`, `categories.jsonl`, `budgets.jsonl`, `recurring.jsonl`이 생성됩니다.
- `recurring.jsonl`은 기존 데이터 보존용이며 반복 거래 명령은 비활성화되어 있습니다.

## 2. 카테고리 추가 및 중복·빈 이름 검증

```sh
ledger category add
```

`카테고리명:`에 `study`를 입력합니다. `[완료] category=study`가 출력되어야 합니다.

```sh
ledger category list
ledger category add
```

다시 `study`를 입력하면 중복 오류가 발생하고 종료 코드는 1이어야 합니다. 이어서 `ledger category add`를 다시 실행해 아무 글자 없이 Enter를 누르면 빈 이름 오류가 발생해야 합니다. `ledger category list`에서 `study`는 한 번만 나와야 합니다.

## 3. 수입·지출 6건 추가

각 거래마다 아래 명령을 새로 실행하고 표의 값을 위에서 아래로 입력합니다. `Enter`는 글자를 입력하지 않고 Enter 키만 누른다는 뜻입니다. 금액에는 쉼표나 `원`을 붙이지 않습니다.

```sh
ledger add
```

| 입력 순서 | A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- | --- |
| 날짜 | 2026-10-01 | 2026-10-10 | 2026-10-10 | 2026-10-15 | 2026-10-20 | 2026-11-01 |
| 타입 | income | expense | expense | expense | expense | expense |
| 카테고리 | salary | food | transport | study | food | food |
| 금액 | 100000 | 15000 | 5000 | 20000 | 10000 | 7000 |
| 메모 | 용돈 | 점심, 친구 | 버스 | 파이썬 교재 | 저녁 | Enter |
| 태그 | allowance | meal,friend | Enter | book | meal | Enter |

예상 결과: 매번 `[저장 완료] id=TX-...`가 출력되고 ID는 서로 다릅니다. F의 메모와 태그는 빈 값으로 저장됩니다. 거래 ID는 실행마다 달라집니다.

이후 수정·삭제를 위해 **B와 D의 실제 ID**를 각각 아래 따옴표 안에 붙여 넣어 실행합니다.

```sh
B_ID='B 저장 시 출력된 실제 TX-... 값'
D_ID='D 저장 시 출력된 실제 TX-... 값'
```

## 4. 최신순 목록, 제한, 재실행 영속성

```sh
ledger list
ledger list --limit 3
python3.12 -m budget_app --data-dir "$SCENARIO_DIR/main" list
```

예상 결과:

- 전체 목록은 **F → E → D → C → B → A**, 총 6건입니다.
- 같은 날짜인 C와 B는 나중에 저장한 C가 먼저 나옵니다.
- `--limit 3`은 F, E, D만 출력합니다.
- 별도 프로세스로 다시 실행한 마지막 명령에서도 6건이 유지됩니다.

## 5. 기간·카테고리·타입·메모·태그 검색

```sh
ledger search --from 2026-10-10 --to 2026-10-10
ledger search --from 2026-10-01 --to 2026-10-31 --category food --type expense --q 점심 --tag meal
ledger search --tag meal
ledger search --tag mea
ledger search --q 없는메모
ledger search
```

| 명령 순서 | 예상 결과 |
| --- | --- |
| 1 | C, B 두 건. 시작일과 종료일을 모두 포함 |
| 2 | B 한 건. 모든 조건을 동시에 만족 |
| 3 | E, B 두 건 |
| 4 | `데이터 없음`. 태그는 부분 문자열이 아닌 정확한 일치 |
| 5 | `데이터 없음` |
| 6 | 전체 6건, F → E → D → C → B → A |

검색 결과가 없어도 정상 종료 코드 0입니다.

## 6. 월별 합계와 예산 경계 검증

```sh
ledger summary --month 2026-10 --top 3
```

예상 출력의 핵심 값:

```text
총 수입: 100000원
총 지출: 50000원
잔액: 50000원
지출 TOP 3
1) food 25000원
2) study 20000원
3) transport 5000원
```

11월 거래 F는 10월 합계에서 제외되어야 합니다.

```sh
ledger budget set --month 2026-10 --amount 60000
ledger summary --month 2026-10
ledger budget set --month 2026-10 --amount 50000
ledger summary --month 2026-10
ledger budget set --month 2026-10 --amount 40000
ledger summary --month 2026-10 --top 2
ledger summary --month 2026-12
```

- 예산 60000: 사용률 `83.3%`, 초과 경고 없음.
- 예산 50000: 사용률 `100.0%`, 초과 경고 없음.
- 예산 40000: 사용률 `125.0%`, `[경고] 예산 초과`, TOP은 food와 study만 표시.
- 12월: `데이터 없음`, 수입·지출·잔액 모두 0원.
- 같은 월 예산은 갱신됩니다. `cat "$SCENARIO_DIR/main/budgets.jsonl"`에서 10월 예산은 40000인 레코드 하나여야 합니다.

## 7. 거래 수정 및 선택 필드 비우기

```sh
ledger update --id "$B_ID" --amount 12000 --memo '점심 수정' --tags meal,work
ledger search --q '점심 수정' --tag work
ledger update --id "$B_ID" --memo "" --tags ""
ledger search --from 2026-10-10 --to 2026-10-10
ledger summary --month 2026-10
```

예상 결과:

- B의 ID·날짜·타입·카테고리는 유지되고 금액은 12000으로 바뀝니다.
- 첫 검색에서 수정된 B 한 건을 확인합니다.
- 두 번째 수정 후 B의 메모와 태그는 비어 있습니다. 같은 날짜 목록은 여전히 C → B입니다.
- 10월 수입 100000, 지출 47000, 잔액 53000, 예산 사용률 117.5%이며 초과 경고가 표시됩니다.

## 8. 사용 중 카테고리 보호, 거래 삭제, 카테고리 삭제

```sh
ledger category remove
```

`study`를 입력합니다. D가 참조하므로 `사용 중인 카테고리는 삭제할 수 없습니다.` 오류와 종료 코드 1을 확인합니다.

```sh
ledger delete --id "$D_ID"
ledger list
ledger category remove
```

다시 `study`를 입력하면 삭제에 성공해야 합니다.

```sh
ledger category list
ledger summary --month 2026-10
ledger delete --id "$D_ID"
echo $?
ledger update --id TX-not-exist --amount 1000
echo $?
```

예상 결과:

- 전체 거래는 F, E, C, B, A의 5건이고 카테고리 목록에서 study가 사라집니다.
- 10월 수입 100000, 지출 27000, 잔액 73000, 사용률 67.5%, 초과 경고 없음.
- TOP은 food 22000원, transport 5000원입니다.
- 이미 삭제한 ID의 재삭제와 없는 ID의 수정은 `없는 데이터` 오류, 종료 코드 1이며 기존 5건은 보존됩니다.

## 9. 잘못된 거래 입력과 데이터 보존

아래 표의 각 행마다 `ledger add`를 새로 실행합니다. 기본 입력은 `2026-10-25 / expense / food / 1000 / 검증 / test`이며, 표의 필드 하나만 교체합니다. `/`는 입력 구분 설명일 뿐 실제로 입력하지 않습니다. **현재 구현은 여섯 필드를 모두 입력받은 후 검증하므로 나머지 질문에도 답해야 합니다.**

| 교체 필드 | 입력값 | 예상 결과 |
| --- | --- | --- |
| 날짜 | 2026-02-30 | 존재하지 않는 날짜 거부 |
| 날짜 | 2026-1-01 | YYYY-MM-DD 형식 오류 |
| 타입 | other | income/expense 외의 값 거부 |
| 카테고리 | missing | 미등록 카테고리 거부 |
| 금액 | 0 | 0원 거부 |
| 금액 | -100 | 음수 거부 |
| 금액 | 1.5 | 소수 거부 |
| 금액 | abc | 숫자가 아닌 값 거부 |

각 명령 직후 `echo $?`는 1이어야 하며 `[오류]`와 `[힌트]`가 출력되어야 합니다. 자동 재입력은 하지 않습니다. 마지막에 `ledger list`와 `ledger summary --month 2026-10`으로 5건, 지출 27000원이 유지되는지 확인합니다.

다음 명령도 각각 실행해 직후 종료 코드를 확인합니다.

```sh
ledger update --id "$B_ID"
ledger update --id "$B_ID" --amount 0
ledger search --from 2026-10-31 --to 2026-10-01
ledger summary --month 2026-13
ledger list --limit 0
ledger budget set --month 2026-10 --amount 0
```

앞의 네 명령은 종료 코드 1, 마지막 두 명령은 인자 파싱 오류로 종료 코드 2입니다. 실패한 수정·예산 설정은 기존 거래와 40000원 예산을 바꾸지 않아야 합니다.

## 10. CSV 내보내기와 별도 장부 가져오기

```sh
ledger export --out "$SCENARIO_DIR/october.csv" --month 2026-10
cat "$SCENARIO_DIR/october.csv"
ledger export --out "$SCENARIO_DIR/day.csv" --from 2026-10-10 --to 2026-10-10
ledger export --out "$SCENARIO_DIR/empty.csv" --month 2026-12
python3.12 -m budget_app --data-dir "$SCENARIO_DIR/restored" import --from "$SCENARIO_DIR/october.csv"
python3.12 -m budget_app --data-dir "$SCENARIO_DIR/restored" list
python3.12 -m budget_app --data-dir "$SCENARIO_DIR/restored" summary --month 2026-10
```

예상 결과:

- october.csv: `4 records`, 헤더 `date,type,category,amount,memo,tags`, E → C → B → A 순서.
- day.csv: `2 records`, C와 B만 포함.
- empty.csv: `0 records`, 헤더만 포함.
- 가져오기: `imported=4, skipped=0`, 종료 코드 0.
- 복원 장부의 거래 내용과 합계는 원본 10월 데이터와 같고 ID는 새로 생성됩니다.
- CSV는 거래만 옮기므로 예산은 복원되지 않습니다. 복원 장부 요약에는 예산 사용률이 없습니다.

## 11. CSV 일부 오류, 인용 문자, 중복 가져오기

아래 블록 전체를 터미널에 붙여 넣어 UTF-8 검증 CSV를 만듭니다. `CSV` 종료 줄도 포함하세요.

```sh
cat > "$SCENARIO_DIR/mixed.csv" <<'CSV'
date,type,category,amount,memo,tags
2026-10-25,expense,food,3000,"간식, 음료","snack,friend"
2026-02-30,expense,food,1000,잘못된 날짜,
2026-10-26,expense,missing,1000,없는 카테고리,
2026-10-27,expense,food,0,잘못된 금액,
CSV
python3.12 -m budget_app --data-dir "$SCENARIO_DIR/csv-check" import --from "$SCENARIO_DIR/mixed.csv"
echo $?
python3.12 -m budget_app --data-dir "$SCENARIO_DIR/csv-check" list
```

예상 결과: CSV 3·4·5행 오류와 힌트, `imported=1, skipped=3`, 종료 코드 1. 정상인 3000원 거래는 저장됩니다. 메모 `간식, 음료`와 태그 `snack,friend`가 유지되어야 합니다.

같은 import 명령을 한 번 더 실행하면 다시 `imported=1, skipped=3`이고 목록은 서로 다른 ID의 거래 2건이 됩니다. 중복을 자동 제거하지 않으므로 실패한 행만 고쳐 별도 파일로 가져와야 합니다.

필수 열만 있는 CSV도 확인합니다.

```sh
cat > "$SCENARIO_DIR/minimal.csv" <<'CSV'
date,type,category,amount
2026-10-28,income,salary,5000
CSV
python3.12 -m budget_app --data-dir "$SCENARIO_DIR/csv-check" import --from "$SCENARIO_DIR/minimal.csv"
```

예상 결과: `imported=1, skipped=0`. 선택 열이 없어도 저장되며 메모와 태그는 비어 있습니다.

## 12. CSV 실패 시 원본 보호

원본 장부의 거래 파일을 비교용으로 복사한 뒤 아래 명령을 각각 실행합니다.

```sh
cp "$SCENARIO_DIR/main/transactions.jsonl" "$SCENARIO_DIR/before.jsonl"
cat > "$SCENARIO_DIR/bad-header.csv" <<'CSV'
date,amount
2026-10-01,1000
CSV
ledger import --from "$SCENARIO_DIR/bad-header.csv"
ledger import --from "$SCENARIO_DIR/does-not-exist.csv"
ledger export --out "$SCENARIO_DIR/no-filter.csv"
ledger export --out "$SCENARIO_DIR/conflict.csv" --month 2026-10 --from 2026-10-01
ledger export --out "$SCENARIO_DIR/main/transactions.jsonl" --month 2026-10
cmp "$SCENARIO_DIR/before.jsonl" "$SCENARIO_DIR/main/transactions.jsonl"
echo $?
```

각 import/export는 오류와 힌트를 출력하고 종료 코드 1이어야 합니다. 마지막 `cmp`는 출력 없이 종료 코드 0이어야 하며, 거래 파일이 바이트 단위로 보존되었다는 뜻입니다.

## 13. 손상된 저장 파일 오류 안내

별도 폴더에서만 손상 파일을 만듭니다.

```sh
mkdir "$SCENARIO_DIR/corrupt"
printf '%s\n' '{bad}' > "$SCENARIO_DIR/corrupt/transactions.jsonl"
python3.12 -m budget_app --data-dir "$SCENARIO_DIR/corrupt" list
echo $?
```

예상 결과: 손상된 JSONL의 경로와 1행 위치, 오류 원인과 복구 안내 및 힌트를 표시하고 종료 코드 1로 종료합니다. Python `Traceback`은 출력하지 않아야 합니다.

## 14. 구현 구조와 자동 검증 보완

콘솔 결과만으로 제너레이터·데코레이터·타입 힌트·원자적 교체의 내부 구조까지 입증할 수는 없습니다. 해당 항목은 코드 확인과 기존 자동 테스트를 함께 사용합니다.

```sh
python3.12 -m unittest discover -s tests -v
```

정상 기준은 모든 테스트 통과 및 `OK`입니다. 기존 테스트에는 CRUD, 재실행 영속성, 검색·요약, CSV, 오류 종료, 교체 실패 시 원본 보존, 12000건 정렬의 Python 메모리 사용 검증이 포함됩니다.

| 과제 항목 | 확인 위치 |
| --- | --- |
| dataclass와 타입 힌트 | budget_app/models.py |
| yield 기반 읽기와 임시 파일 교체 | budget_app/storage.py |
| 필터링·정렬·집계 | budget_app/service.py |
| 실제 적용된 예외 처리 데코레이터 | budget_app/cli.py의 handle_errors와 main |

백업·반복 거래·고정 너비 표 정렬은 현재 비활성화된 선택 과제이므로 정상 동작 시나리오에서 제외합니다. 검증 종료 후 임시 데이터 위치는 `echo "$SCENARIO_DIR"`로 확인할 수 있습니다.
