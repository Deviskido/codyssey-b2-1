# 과제 요구사항 검증용 콘솔 입출력 시나리오

현재 `budget_app` 코드와 `requirements.txt`를 기준으로 작성했습니다. 아래 앱 명령은 현재 코드를 별도 임시 작업 폴더에서 실제 실행하여 출력과 종료 코드를 확인했습니다. ID는 설명용 이름으로 바꾸어 표기했습니다.

## 실행 전 안내

- `README.md`와 `budget_app` 폴더가 있는 프로젝트 루트에서 실행합니다. Python 3.10 이상이 필요하며 이 문서는 설치된 `python3.12`를 사용합니다.
- 별칭·래퍼 함수·셸 변수 없이 매번 `python3.12 -m budget_app ...` 전체 명령을 입력합니다.
- **1번부터 순서대로 한 번씩** 진행합니다. 앞 단계의 저장·수정·삭제 결과를 다음 단계에서 사용합니다.
- 테스트 저장 위치는 `./console-test/main`입니다. 기존 `./data`의 내용에 따라 결과가 달라지지 않도록 별도 폴더를 지정합니다. 시작 전에 `console-test` 폴더가 없는지 확인하세요. 이미 있다면 기존 폴더의 이름을 바꾸거나 문서의 모든 `console-test` 경로를 새로운 이름으로 바꾸세요.
- `sh` 블록은 실행 명령이고, `text` 블록은 예상 화면입니다. 대화형 화면에서는 질문 뒤에 적힌 값만 입력하고 Enter를 누릅니다. 질문 뒤가 비어 있으면 Enter만 누릅니다.
- **`TX-A`부터 `TX-F`는 실제 ID가 아닌 설명용 표기입니다.** 실제로는 `TX-` 뒤에 32자리 문자열이 출력됩니다. B와 D의 실제 ID를 기록하고, 이후 명령의 `TX-B`, `TX-D`를 그 값으로 직접 교체하세요. `TX-가져오기N`도 새로 생성되는 ID를 뜻합니다.
- 종료 코드는 해당 명령 직후 `echo $?`를 실행해 확인합니다. 정상은 0, 입력·처리 오류는 1, 명령줄 형식 오류는 2입니다. 오류 테스트에서도 Python 스택트레이스(`Traceback`)는 없어야 합니다.

## 1. 최초 실행과 저장 폴더 자동 생성

확인 요구사항: 패키지 실행, 빈 목록 안내, 기본 카테고리 생성, 저장 위치 지정.

```sh
python3.12 -m budget_app --data-dir ./console-test/main list
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
데이터 없음
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main category list
```

예상 화면:

```text
- food
- transport
- rent
- salary
- etc
```

종료 코드: `0`.

```sh
ls -1 ./console-test/main
```

예상 출력:

```text
budgets.jsonl
categories.jsonl
recurring.jsonl
transactions.jsonl
```

필수 저장 파일 3개와 기존 반복 규칙 보존용 파일 1개가 생성됩니다.

## 2. 카테고리 추가·중복·빈 이름 검증

```sh
python3.12 -m budget_app --data-dir ./console-test/main category add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리명: study
[완료] category=study
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main category list
```

예상 화면:

```text
- food
- transport
- rent
- salary
- etc
- study
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main category add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리명: study
[오류] 중복 카테고리입니다. 다른 이름을 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main category add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리명: 
[오류] 카테고리명을 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

## 3. 수입·지출 추가: 대화형 입력과 고유 ID

A부터 F까지 순서대로 추가합니다. 날짜, 타입, 카테고리, 양수 금액, 선택 메모·태그를 검증할 기본 데이터입니다.

### 거래 A

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc, study
날짜(YYYY-MM-DD): 2026-10-01
타입(income/expense): income
카테고리: salary
금액(양수 정수): 100000
메모(선택): 용돈
태그(쉼표 구분, 선택): allowance
[저장 완료] id=TX-A
```

종료 코드: `0`.

### 거래 B

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc, study
날짜(YYYY-MM-DD): 2026-10-10
타입(income/expense): expense
카테고리: food
금액(양수 정수): 15000
메모(선택): 점심, 친구
태그(쉼표 구분, 선택): meal,friend
[저장 완료] id=TX-B
```

종료 코드: `0`.

### 거래 C

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc, study
날짜(YYYY-MM-DD): 2026-10-10
타입(income/expense): expense
카테고리: transport
금액(양수 정수): 5000
메모(선택): 버스
태그(쉼표 구분, 선택): 
[저장 완료] id=TX-C
```

종료 코드: `0`.

### 거래 D

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc, study
날짜(YYYY-MM-DD): 2026-10-15
타입(income/expense): expense
카테고리: study
금액(양수 정수): 20000
메모(선택): 파이썬 교재
태그(쉼표 구분, 선택): book
[저장 완료] id=TX-D
```

종료 코드: `0`.

### 거래 E

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc, study
날짜(YYYY-MM-DD): 2026-10-20
타입(income/expense): expense
카테고리: food
금액(양수 정수): 10000
메모(선택): 저녁
태그(쉼표 구분, 선택): meal
[저장 완료] id=TX-E
```

종료 코드: `0`.

### 거래 F

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc, study
날짜(YYYY-MM-DD): 2026-11-01
타입(income/expense): expense
카테고리: food
금액(양수 정수): 7000
메모(선택): 
태그(쉼표 구분, 선택): 
[저장 완료] id=TX-F
```

종료 코드: `0`.

## 4. 최신순·동일 날짜 순서·출력 제한·재실행

각 명령은 새 프로세스에서 실행됩니다. 앞서 종료된 add 프로세스의 데이터가 다시 조회되면 영속성을 확인할 수 있습니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/main list
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-F | 2026-11-01 | expense | food | 7000 |  / 
TX-E | 2026-10-20 | expense | food | 10000 | 저녁 / meal
TX-D | 2026-10-15 | expense | study | 20000 | 파이썬 교재 / book
TX-C | 2026-10-10 | expense | transport | 5000 | 버스 / 
TX-B | 2026-10-10 | expense | food | 15000 | 점심, 친구 / meal,friend
TX-A | 2026-10-01 | income | salary | 100000 | 용돈 / allowance
```

종료 코드: `0`.

날짜가 최신인 F부터 표시됩니다. 같은 10월 10일의 거래는 나중에 저장한 C가 B보다 먼저 나옵니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/main list --limit 3
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-F | 2026-11-01 | expense | food | 7000 |  / 
TX-E | 2026-10-20 | expense | food | 10000 | 저녁 / meal
TX-D | 2026-10-15 | expense | study | 20000 | 파이썬 교재 / book
```

종료 코드: `0`.

기본 제한은 20건이며 현재는 전체 6건이 보입니다. `--limit 3`에서는 3건만 보여야 합니다.

## 5. 검색: 기간·카테고리·타입·메모·태그

기간 양 끝을 포함하고 여러 검색 조건은 AND로 적용됩니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/main search --from 2026-10-10 --to 2026-10-10
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-C | 2026-10-10 | expense | transport | 5000 | 버스 / 
TX-B | 2026-10-10 | expense | food | 15000 | 점심, 친구 / meal,friend
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main search --from 2026-10-01 --to 2026-10-31 --category food --type expense --q '점심' --tag meal
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-B | 2026-10-10 | expense | food | 15000 | 점심, 친구 / meal,friend
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main search --tag meal
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-E | 2026-10-20 | expense | food | 10000 | 저녁 / meal
TX-B | 2026-10-10 | expense | food | 15000 | 점심, 친구 / meal,friend
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main search --tag mea
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
데이터 없음
```

종료 코드: `0`.

`mea`는 `meal`의 일부이지만 태그 검색은 정확히 일치해야 합니다. 결과가 없는 검색도 정상 종료입니다.

## 6. 월별 합계·카테고리 TOP·빈 월

10월 수입 100000원, 지출 50000원입니다. 11월 거래 F는 제외됩니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/main summary --month 2026-10 --top 3
```

예상 화면:

```text
총 수입: 100000원
총 지출: 50000원
잔액: 50000원
지출 TOP 3
1) food 25000원
2) study 20000원
3) transport 5000원
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main summary --month 2026-12
```

예상 화면:

```text
데이터 없음
총 수입: 0원
총 지출: 0원
잔액: 0원
지출 TOP 3
```

종료 코드: `0`.

## 7. 예산 설정·갱신·사용률·초과 경고

지출이 예산보다 클 때만 경고합니다. 예산과 지출이 같으면 경고하지 않습니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/main budget set --month 2026-10 --amount 60000
```

예상 화면:

```text
[저장 완료] 2026-10 예산 60000원
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main summary --month 2026-10 --top 2
```

예상 화면:

```text
총 수입: 100000원
총 지출: 50000원
잔액: 50000원
예산: 60000원 (사용률 83.3%)
지출 TOP 2
1) food 25000원
2) study 20000원
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main budget set --month 2026-10 --amount 50000
```

예상 화면:

```text
[저장 완료] 2026-10 예산 50000원
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main summary --month 2026-10 --top 2
```

예상 화면:

```text
총 수입: 100000원
총 지출: 50000원
잔액: 50000원
예산: 50000원 (사용률 100.0%)
지출 TOP 2
1) food 25000원
2) study 20000원
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main budget set --month 2026-10 --amount 40000
```

예상 화면:

```text
[저장 완료] 2026-10 예산 40000원
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main summary --month 2026-10 --top 2
```

예상 화면:

```text
총 수입: 100000원
총 지출: 50000원
잔액: 50000원
예산: 40000원 (사용률 125.0%)
[경고] 예산 초과
지출 TOP 2
1) food 25000원
2) study 20000원
```

종료 코드: `0`.

```sh
cat ./console-test/main/budgets.jsonl
```

예상 파일 내용:

```text
{"month": "2026-10", "amount": 40000}
```

같은 월의 예산은 누적 추가되지 않고 40000원으로 갱신되어 한 줄만 남아야 합니다.

## 8. CSV 내보내기: 월·기간·빈 결과

수정·삭제하기 전의 10월 5건을 내보냅니다. 쉼표가 있는 메모와 태그의 CSV 인용 처리도 확인합니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/main export --out ./console-test/october.csv --month 2026-10
```

예상 화면:

```text
[완료] ./console-test/october.csv (5 records)
```

종료 코드: `0`.

```sh
cat ./console-test/october.csv
```

예상 파일 내용:

```text
date,type,category,amount,memo,tags
2026-10-20,expense,food,10000,저녁,meal
2026-10-15,expense,study,20000,파이썬 교재,book
2026-10-10,expense,transport,5000,버스,
2026-10-10,expense,food,15000,"점심, 친구","meal,friend"
2026-10-01,income,salary,100000,용돈,allowance
```

```sh
python3.12 -m budget_app --data-dir ./console-test/main export --out ./console-test/day.csv --from 2026-10-10 --to 2026-10-10
```

예상 화면:

```text
[완료] ./console-test/day.csv (2 records)
```

종료 코드: `0`.

```sh
cat ./console-test/day.csv
```

예상 파일 내용:

```text
date,type,category,amount,memo,tags
2026-10-10,expense,transport,5000,버스,
2026-10-10,expense,food,15000,"점심, 친구","meal,friend"
```

```sh
python3.12 -m budget_app --data-dir ./console-test/main export --out ./console-test/empty.csv --month 2026-12
```

예상 화면:

```text
[완료] ./console-test/empty.csv (0 records)
```

종료 코드: `0`.

```sh
cat ./console-test/empty.csv
```

예상 파일 내용:

```text
date,type,category,amount,memo,tags
```

## 9. CSV 가져오기: 새 장부에 복원

CSV에는 study 거래가 있으므로 복원 대상 장부에도 해당 카테고리를 먼저 등록합니다. CSV는 카테고리 정의나 예산을 복원하지 않습니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/restored category add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리명: study
[완료] category=study
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/restored import --from ./console-test/october.csv
```

예상 화면:

```text
[완료] imported=5, skipped=0
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/restored list
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-가져오기1 | 2026-10-20 | expense | food | 10000 | 저녁 / meal
TX-가져오기2 | 2026-10-15 | expense | study | 20000 | 파이썬 교재 / book
TX-가져오기3 | 2026-10-10 | expense | food | 15000 | 점심, 친구 / meal,friend
TX-가져오기4 | 2026-10-10 | expense | transport | 5000 | 버스 / 
TX-가져오기5 | 2026-10-01 | income | salary | 100000 | 용돈 / allowance
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/restored summary --month 2026-10
```

예상 화면:

```text
총 수입: 100000원
총 지출: 50000원
잔액: 50000원
지출 TOP 3
1) food 25000원
2) study 20000원
3) transport 5000원
```

종료 코드: `0`.

거래 내용과 합계는 원본과 같고 ID는 새로 생성됩니다. 예산은 가져오지 않으므로 예산 사용률 줄은 없습니다.

## 10. 거래 수정·ID 유지·선택 필드 비우기

아래 명령의 `TX-B`는 3번에서 기록한 B의 실제 ID로 바꿉니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/main update --id TX-B --amount 12000 --memo '점심 수정' --tags meal,work
```

예상 화면:

```text
[수정 완료] id=TX-B
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main search --q '점심 수정' --tag work
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-B | 2026-10-10 | expense | food | 12000 | 점심 수정 / meal,work
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main update --id TX-B --memo '' --tags ''
```

예상 화면:

```text
[수정 완료] id=TX-B
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main search --from 2026-10-10 --to 2026-10-10
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-C | 2026-10-10 | expense | transport | 5000 | 버스 / 
TX-B | 2026-10-10 | expense | food | 12000 |  /
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main summary --month 2026-10
```

예상 화면:

```text
총 수입: 100000원
총 지출: 47000원
잔액: 53000원
예산: 40000원 (사용률 117.5%)
[경고] 예산 초과
지출 TOP 3
1) food 22000원
2) study 20000원
3) transport 5000원
```

종료 코드: `0`.

B의 ID·날짜·타입·카테고리는 유지됩니다. 동일 날짜의 저장 순서는 수정 후에도 C → B이며, 비운 메모·태그는 빈 값으로 출력됩니다.

## 11. 사용 중 카테고리 보호·거래 삭제·없는 ID

`TX-D`는 D의 실제 ID로 바꿉니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/main category remove
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리명: study
[오류] 사용 중인 카테고리는 삭제할 수 없습니다.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main delete --id TX-D
```

예상 화면:

```text
[삭제 완료] id=TX-D
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main category remove
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리명: study
[완료] category=study
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main category list
```

예상 화면:

```text
- food
- transport
- rent
- salary
- etc
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main delete --id TX-D
```

예상 화면:

```text
[오류] 없는 데이터입니다. list에서 ID를 확인하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main update --id TX-not-exist --amount 1000
```

예상 화면:

```text
[오류] 없는 데이터입니다. list에서 ID를 확인하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main list
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-F | 2026-11-01 | expense | food | 7000 |  / 
TX-E | 2026-10-20 | expense | food | 10000 | 저녁 / meal
TX-C | 2026-10-10 | expense | transport | 5000 | 버스 / 
TX-B | 2026-10-10 | expense | food | 12000 |  / 
TX-A | 2026-10-01 | income | salary | 100000 | 용돈 / allowance
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main summary --month 2026-10
```

예상 화면:

```text
총 수입: 100000원
총 지출: 27000원
잔액: 73000원
예산: 40000원 (사용률 67.5%)
지출 TOP 3
1) food 22000원
2) transport 5000원
```

종료 코드: `0`.

이 시점의 기준 상태: 전체 5건, 10월 수입 100000원, 지출 27000원, 잔액 73000원, 예산 40000원입니다. 이후 오류 검증으로 이 값이 바뀌면 안 됩니다.

## 12. 잘못된 거래 입력 거부

현재 코드는 여섯 항목을 모두 입력받은 뒤 검증합니다. 잘못된 값을 입력해도 남은 질문에 답해야 오류가 표시됩니다. 자동으로 재입력을 요구하지 않고 오류 종료합니다.

### 존재하지 않는 날짜

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc
날짜(YYYY-MM-DD): 2026-02-30
타입(income/expense): expense
카테고리: food
금액(양수 정수): 1000
메모(선택): 검증
태그(쉼표 구분, 선택): test
[오류] day is out of range for month
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

### 날짜 형식 오류

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc
날짜(YYYY-MM-DD): 2026-1-01
타입(income/expense): expense
카테고리: food
금액(양수 정수): 1000
메모(선택): 검증
태그(쉼표 구분, 선택): test
[오류] 날짜 형식 오류. YYYY-MM-DD로 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

### 허용되지 않은 타입

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc
날짜(YYYY-MM-DD): 2026-10-25
타입(income/expense): other
카테고리: food
금액(양수 정수): 1000
메모(선택): 검증
태그(쉼표 구분, 선택): test
[오류] type은 income 또는 expense로 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

### 미등록 카테고리

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc
날짜(YYYY-MM-DD): 2026-10-25
타입(income/expense): expense
카테고리: missing
금액(양수 정수): 1000
메모(선택): 검증
태그(쉼표 구분, 선택): test
[오류] 등록되지 않은 category입니다. category add로 등록하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

### 0원

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc
날짜(YYYY-MM-DD): 2026-10-25
타입(income/expense): expense
카테고리: food
금액(양수 정수): 0
메모(선택): 검증
태그(쉼표 구분, 선택): test
[오류] 금액/개수는 양수 정수로 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

### 음수 금액

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc
날짜(YYYY-MM-DD): 2026-10-25
타입(income/expense): expense
카테고리: food
금액(양수 정수): -100
메모(선택): 검증
태그(쉼표 구분, 선택): test
[오류] 금액/개수는 양수 정수로 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

### 소수 금액

```sh
python3.12 -m budget_app --data-dir ./console-test/main add
```

예상 화면 (질문 뒤의 값은 직접 입력합니다):

```text
카테고리: food, transport, rent, salary, etc
날짜(YYYY-MM-DD): 2026-10-25
타입(income/expense): expense
카테고리: food
금액(양수 정수): 1.5
메모(선택): 검증
태그(쉼표 구분, 선택): test
[오류] 금액/개수는 양수 정수로 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

## 13. 옵션 오류·실패한 수정의 원본 보존

각 명령 직후 `echo $?`로 명시한 종료 코드를 확인합니다. 사용법에 표시되는 실행 파일 경로와 줄바꿈은 환경에 따라 다를 수 있습니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/main update --id TX-B
```

예상 화면:

```text
[오류] 수정할 필드를 하나 이상 지정하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main update --id TX-B --amount 0
```

예상 화면:

```text
[오류] 금액/개수는 양수 정수로 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main search --from 2026-10-31 --to 2026-10-01
```

예상 화면:

```text
[오류] --from은 --to보다 늦을 수 없습니다.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main summary --month 2026-13
```

예상 화면:

```text
[오류] time data '2026-13-01' does not match format '%Y-%m-%d'
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main list --limit 0
```

예상 화면:

```text
usage: __main__.py list [-h] [--data-dir DATA_DIR] [--limit LIMIT]
[오류] argument --limit: invalid positive value: '0'
[힌트] --help로 사용법을 확인하세요.
```

종료 코드: `2`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main budget set --month 2026-10 --amount 0
```

예상 화면:

```text
usage: __main__.py budget set [-h] --month MONTH --amount AMOUNT
[오류] argument --amount: invalid positive value: '0'
[힌트] --help로 사용법을 확인하세요.
```

종료 코드: `2`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main delete
```

예상 화면:

```text
usage: __main__.py delete [-h] [--data-dir DATA_DIR] --id ID
[오류] the following arguments are required: --id
[힌트] --help로 사용법을 확인하세요.
```

종료 코드: `2`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main list
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-F | 2026-11-01 | expense | food | 7000 |  / 
TX-E | 2026-10-20 | expense | food | 10000 | 저녁 / meal
TX-C | 2026-10-10 | expense | transport | 5000 | 버스 / 
TX-B | 2026-10-10 | expense | food | 12000 |  / 
TX-A | 2026-10-01 | income | salary | 100000 | 용돈 / allowance
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main summary --month 2026-10
```

예상 화면:

```text
총 수입: 100000원
총 지출: 27000원
잔액: 73000원
예산: 40000원 (사용률 67.5%)
지출 TOP 3
1) food 22000원
2) transport 5000원
```

종료 코드: `0`.

## 14. CSV 일부 행 오류·선택 열 생략·중복 가져오기

별도 `csv-check` 장부를 사용합니다. 올바른 행은 저장하고 잘못된 행은 건너뛰는 정책을 확인합니다.

아래 블록 전체를 터미널에 붙여 넣어 테스트 파일을 만듭니다. 마지막 `CSV` 줄도 포함합니다.

```sh
cat > ./console-test/mixed.csv <<'CSV'
date,type,category,amount,memo,tags
2026-10-25,expense,food,3000,"간식, 음료","snack,friend"
2026-02-30,expense,food,1000,잘못된 날짜,
2026-10-26,expense,missing,1000,없는 카테고리,
2026-10-27,expense,food,0,잘못된 금액,
CSV
```

```sh
python3.12 -m budget_app --data-dir ./console-test/csv-check import --from ./console-test/mixed.csv
```

예상 화면:

```text
[오류] CSV 3행: day is out of range for month [힌트] 행을 수정 후 다시 가져오세요.
[오류] CSV 4행: 등록되지 않은 category입니다. category add로 등록하세요. [힌트] 행을 수정 후 다시 가져오세요.
[오류] CSV 5행: 금액/개수는 양수 정수로 입력하세요. [힌트] 행을 수정 후 다시 가져오세요.
[완료] imported=1, skipped=3
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/csv-check list
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-가져오기6 | 2026-10-25 | expense | food | 3000 | 간식, 음료 / snack,friend
```

종료 코드: `0`.

헤더를 1행으로 세므로 오류 위치는 3·4·5행입니다. 일부 저장에 성공했어도 건너뛴 행이 있으면 종료 코드가 1입니다.

```sh
python3.12 -m budget_app --data-dir ./console-test/csv-check import --from ./console-test/mixed.csv
```

예상 화면:

```text
[오류] CSV 3행: day is out of range for month [힌트] 행을 수정 후 다시 가져오세요.
[오류] CSV 4행: 등록되지 않은 category입니다. category add로 등록하세요. [힌트] 행을 수정 후 다시 가져오세요.
[오류] CSV 5행: 금액/개수는 양수 정수로 입력하세요. [힌트] 행을 수정 후 다시 가져오세요.
[완료] imported=1, skipped=3
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/csv-check list
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-가져오기7 | 2026-10-25 | expense | food | 3000 | 간식, 음료 / snack,friend
TX-가져오기6 | 2026-10-25 | expense | food | 3000 | 간식, 음료 / snack,friend
```

종료 코드: `0`.

같은 파일을 다시 가져오면 정상 행이 다른 ID로 한 번 더 추가됩니다. 실패한 행만 수정해 별도 파일로 가져오는 것이 현재 정책에 맞습니다.

아래 블록 전체를 터미널에 붙여 넣어 테스트 파일을 만듭니다. 마지막 `CSV` 줄도 포함합니다.

```sh
cat > ./console-test/minimal.csv <<'CSV'
date,type,category,amount
2026-10-28,income,salary,5000
CSV
```

```sh
python3.12 -m budget_app --data-dir ./console-test/csv-check import --from ./console-test/minimal.csv
```

예상 화면:

```text
[완료] imported=1, skipped=0
```

종료 코드: `0`.

```sh
python3.12 -m budget_app --data-dir ./console-test/csv-check list
```

예상 화면:

```text
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
TX-가져오기8 | 2026-10-28 | income | salary | 5000 |  / 
TX-가져오기7 | 2026-10-25 | expense | food | 3000 | 간식, 음료 / snack,friend
TX-가져오기6 | 2026-10-25 | expense | food | 3000 | 간식, 음료 / snack,friend
```

종료 코드: `0`.

## 15. CSV 전체 실패와 저장 파일 덮어쓰기 차단

먼저 비교용 복사본을 만듭니다. 성공 시 cp는 출력 없이 종료합니다.

```sh
cp ./console-test/main/transactions.jsonl ./console-test/before.jsonl
```

아래 블록 전체를 터미널에 붙여 넣어 테스트 파일을 만듭니다. 마지막 `CSV` 줄도 포함합니다.

```sh
cat > ./console-test/bad-header.csv <<'CSV'
date,amount
2026-10-01,1000
CSV
```

```sh
python3.12 -m budget_app --data-dir ./console-test/main import --from ./console-test/bad-header.csv
```

예상 화면:

```text
[오류] CSV 필수 헤더: date,type,category,amount를 확인하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main import --from ./console-test/does-not-exist.csv
```

예상 화면:

```text
[오류] [Errno 2] No such file or directory: './console-test/does-not-exist.csv'
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main export --out ./console-test/no-filter.csv
```

예상 화면:

```text
[오류] --month 또는 --from/--to 조건을 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main export --out ./console-test/conflict.csv --month 2026-10 --from 2026-10-01
```

예상 화면:

```text
[오류] 월과 기간 조건 중 하나만 사용하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

```sh
python3.12 -m budget_app --data-dir ./console-test/main export --out ./console-test/main/transactions.jsonl --month 2026-10
```

예상 화면:

```text
[오류] 저장 파일을 덮어쓸 수 없습니다. 다른 CSV 경로를 입력하세요.
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
```

종료 코드: `1`.

원본 보존 확인 명령:

```sh
cmp ./console-test/before.jsonl ./console-test/main/transactions.jsonl
echo $?
```

예상 결과: `cmp`는 아무 내용도 출력하지 않고 `echo $?`가 `0`을 출력합니다. 이는 거래 파일이 바이트 단위로 동일하다는 뜻입니다.

## 16. 손상된 JSONL 오류 처리

별도 폴더에만 손상 파일을 만듭니다.

```sh
mkdir ./console-test/corrupt
printf '%s\n' '{bad}' > ./console-test/corrupt/transactions.jsonl
```

```sh
python3.12 -m budget_app --data-dir ./console-test/corrupt list
```

예상 화면:

```text
[오류] console-test/corrupt/transactions.jsonl:1 손상된 JSONL. 백업을 복구하세요: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.
ID | DATE | TYPE | CATEGORY | AMOUNT | MEMO / TAGS
```

종료 코드: `1`.

## 17. 모든 명령의 도움말

아래 명령은 각각 사용법을 출력하고 종료 코드 0이어야 합니다. 아래 목록은 실제 실행하여 모두 확인했습니다. 출력되는 옵션은 README의 파서 트리와 비교할 수 있습니다.

```sh
python3.12 -m budget_app --help
python3.12 -m budget_app add --help
python3.12 -m budget_app list --help
python3.12 -m budget_app search --help
python3.12 -m budget_app update --help
python3.12 -m budget_app delete --help
python3.12 -m budget_app summary --help
python3.12 -m budget_app budget --help
python3.12 -m budget_app budget set --help
python3.12 -m budget_app category --help
python3.12 -m budget_app category add --help
python3.12 -m budget_app category list --help
python3.12 -m budget_app category remove --help
python3.12 -m budget_app import --help
python3.12 -m budget_app export --help
```

## 18. 콘솔 동작만으로 확인하기 어려운 구조 요구사항

위 입출력은 기능과 오류 처리를 확인합니다. 제너레이터 사용, 데코레이터 적용, 타입 힌트, 클래스·모듈 분리와 쓰기 실패 시 원자성은 콘솔 화면만으로 입증할 수 없으므로 코드와 기존 자동 테스트를 함께 확인합니다.

```sh
python3.12 -m unittest discover -s tests -v
```

정상 기준: 11개 테스트가 통과하고 마지막에 `OK`를 출력합니다. 실행 시간은 환경에 따라 달라집니다. 테스트는 자체 임시 폴더를 사용합니다.

| 과제 요구사항 | 확인 단계 또는 코드 |
| --- | --- |
| 대화형 거래 추가, 고유 ID, 선택 입력 | 3번 |
| 최신순·limit·영속성 | 4번 |
| 기간·카테고리·타입·메모·태그 검색 | 5번 |
| 월별 합계·지출 TOP·빈 월 | 6번 |
| 예산 저장·조회·초과 경고 | 7번 |
| CSV 월/기간 출력·가져오기·오류 행 처리 | 8·9·14·15번 |
| 옵션 방식 수정·삭제·없는 ID | 10·11·13번 |
| 카테고리 추가·목록·삭제·사용 중 보호 | 2·11번 |
| 잘못된 입력·오류 힌트·종료 코드 | 12·13·14·15·16번 |
| 저장 파일 3개 이상·자동 생성·경로 옵션 | 1번 |
| 모든 명령 도움말 | 17번 |
| dataclass·타입 힌트 | models.py의 Transaction 및 함수 선언 |
| 최소 2개 클래스·3개 모듈 | Transaction, JsonStore, TransactionRepository, BudgetService 및 cli/models/storage/service.py |
| 제너레이터 스트리밍 | storage.py의 records(), service.py의 filtered(), ordered() |
| 공통 관심사 데코레이터 | cli.py의 handle_errors와 main의 @handle_errors |
| 원자적 교체·쓰기 실패 시 원본 보존 | storage.py의 replace(), 기존 test_atomic_failure_preserves_original |
| 대용량 정렬 메모리 검증 | 기존 test_large_ordered_query_bounded_python_memory |
| 실행 방법·저장 형식·CSV 계약 문서화 | README.md |

백업, 반복 거래, 고정 너비 표 정렬은 선택 과제로 현재 코드에서 비활성화되어 있으므로 필수 기능 검증에서 제외합니다.

