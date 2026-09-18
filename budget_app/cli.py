"""Command parsing, interactive input, and user-facing presentation."""
import argparse
import csv
from functools import wraps
import sqlite3
import sys
from typing import Any, Callable
import unicodedata

from .models import positive
from .service import BudgetService


def handle_errors(function: Callable[..., int]) -> Callable[..., int]:
    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> int:
        try:
            return function(*args, **kwargs)
        except (ValueError, TypeError, KeyError, OSError, EOFError, csv.Error, sqlite3.Error) as error:
            print(f'[오류] {error}\n[힌트] 입력값, 파일 형식 및 접근 권한을 확인하세요. --help로 사용법을 확인할 수 있습니다.', file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print('[오류] 입력을 취소했습니다. [힌트] 명령을 다시 실행하세요.', file=sys.stderr)
            return 130
    return wrapped


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f'[오류] {message}\n[힌트] --help로 사용법을 확인하세요.\n')


def parser() -> argparse.ArgumentParser:
    root = Parser(description='파일 기반 용돈 기입장')
    root.add_argument('--data-dir', default='./data', help='저장 폴더 (기본: ./data)')
    commands = root.add_subparsers(dest='command', required=True)
    def command(name: str, help_text: str) -> argparse.ArgumentParser:
        result = commands.add_parser(name, help=help_text, description=help_text)
        result.add_argument('--data-dir', default=argparse.SUPPRESS, help='저장 폴더')
        return result
    def period(p: argparse.ArgumentParser) -> None:
        p.add_argument('--from', dest='start', help='시작 날짜 YYYY-MM-DD (포함)')
        p.add_argument('--to', dest='end', help='종료 날짜 YYYY-MM-DD (포함)')
    command('add', '대화형 거래 추가')
    p = command('list', '최신순 거래 목록')
    p.add_argument('--limit', type=positive, default=20, help='최대 출력 건수 (기본: 20)')
    p = command('search', '조건을 모두 만족하는 거래 검색')
    period(p)
    p.add_argument('--category')
    p.add_argument('--type', choices=['income', 'expense'])
    p.add_argument('--q', help='메모 키워드 (대소문자 구분)')
    p.add_argument('--tag')
    p = command('update', '옵션 기반 거래 수정')
    p.add_argument('--id', required=True)
    for field in ['date', 'type', 'category', 'amount', 'memo', 'tags']:
        p.add_argument('--' + field)
    p = command('delete', 'ID로 거래 삭제')
    p.add_argument('--id', required=True)
    p = command('summary', '월별 요약 및 예산 조회')
    p.add_argument('--month', required=True)
    p.add_argument('--top', type=positive, default=3)
    p = command('budget', '월 예산 설정')
    sub = p.add_subparsers(dest='action', required=True)
    setting = sub.add_parser('set', help='월 예산 저장/갱신')
    setting.add_argument('--month', required=True)
    setting.add_argument('--amount', type=positive, required=True)
    p = command('category', '카테고리 관리')
    sub = p.add_subparsers(dest='action', required=True)
    for action in ['add', 'list', 'remove']:
        sub.add_parser(action)
    p = command('import', 'CSV 일괄 가져오기')
    p.add_argument('--from', dest='source', required=True)
    p = command('export', '조건에 맞는 거래 CSV 내보내기')
    p.add_argument('--out', required=True)
    p.add_argument('--month')
    period(p)
    command('backup', '타임스탬프 ZIP 백업 생성')
    p = command('recurring', '반복 거래 규칙 및 월별 생성')
    sub = p.add_subparsers(dest='action', required=True)
    sub.add_parser('add', help='규칙 대화형 등록')
    sub.add_parser('list', help='등록 규칙 조회')
    generate = sub.add_parser('generate', help='지정 월의 거래 생성')
    generate.add_argument('--month', required=True)
    return root


def inputs(include_date: bool = True) -> dict[str, str]:
    fields = [('date', '날짜(YYYY-MM-DD)'), ('type', '타입(income/expense)'),
              ('category', '카테고리'), ('amount', '금액(양수 정수)'),
              ('memo', '메모(선택)'), ('tags', '태그(쉼표 구분, 선택)')]
    return {key: input(label + ': ').strip() for key, label in fields if include_date or key != 'date'}


def cell(value: Any, width: int) -> str:
    text = str(value).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    result = ''
    used = 0
    for char in text:
        size = 0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1
        if used + size > width:
            break
        result += char
        used += size
    return result + ' ' * (width - used)


def show_transactions(records: Any) -> None:
    print(f"{'ID':<43} | {'DATE':<10} | {'TYPE':<7} | {'CATEGORY':<16} | {'AMOUNT':>12} | MEMO / TAGS")
    count = 0
    for r in records:
        print(f"{r['id']:<43} | {r['date']} | {r['type']:<7} | {cell(r['category'], 16)} | {r['amount']:>12} | {cell(r['memo'], 30)} / {','.join(r['tags'])}")
        count += 1
    if not count:
        print('데이터 없음')


@handle_errors
def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    service = BudgetService(args.data_dir)
    values = vars(args)
    command = args.command
    if command == 'add':
        print('카테고리: ' + ', '.join(service.category_names()))
        print('[저장 완료] id=' + service.add(inputs()).id)
    elif command == 'list':
        show_transactions(service.ordered(limit=args.limit))
    elif command == 'search':
        show_transactions(service.ordered(**{k: values[k] for k in ['start', 'end', 'category', 'type', 'q', 'tag']}))
    elif command == 'update':
        changes = {k: values[k] for k in ['date', 'type', 'category', 'amount', 'memo', 'tags'] if values[k] is not None}
        if not changes:
            raise ValueError('수정할 필드를 하나 이상 지정하세요.')
        service.update(args.id, changes)
        print('[수정 완료] id=' + args.id)
    elif command == 'delete':
        service.transactions.change(args.id, None)
        print('[삭제 완료] id=' + args.id)
    elif command == 'category':
        if args.action == 'list':
            for name in service.category_names():
                print('- ' + name)
        else:
            name = input('카테고리명: ').strip()
            service.category_change(name, remove=args.action == 'remove')
            print('[완료] category=' + name)
    elif command == 'budget':
        service.set_budget(args.month, args.amount)
        print(f'[저장 완료] {args.month} 예산 {args.amount}원')
    elif command == 'summary':
        result = service.summary(args.month, args.top)
        if not result['count']:
            print('데이터 없음')
        for title, key in [('총 수입', 'income'), ('총 지출', 'expense'), ('잔액', 'balance')]:
            print(f'{title}: {result[key]}원')
        if result['budget'] is not None:
            print(f"예산: {result['budget']}원 (사용률 {result['expense'] / result['budget'] * 100:.1f}%)")
            if result['expense'] > result['budget']:
                print('[경고] 예산 초과')
        print(f'지출 TOP {args.top}')
        for index, (category, amount) in enumerate(result['top'], 1):
            print(f'{index}) {cell(category, 16)} {amount:>12}원')
    elif command == 'import':
        imported, skipped = service.import_csv(args.source)
        print(f'[완료] imported={imported}, skipped={skipped}')
        return int(skipped > 0)
    elif command == 'export':
        count = service.export_csv(args.out, **{k: values[k] for k in ['month', 'start', 'end']})
        print(f'[완료] {args.out} ({count} records)')
    elif command == 'backup':
        print('[완료] ' + str(service.backup()))
    elif command == 'recurring':
        if args.action == 'add':
            name = input('규칙명: ').strip()
            day = positive(input('매월 날짜(1~31): ').strip())
            service.add_rule(name, day, inputs(include_date=False))
            print('[저장 완료] ' + name)
        elif args.action == 'list':
            for rule in service.rules.records():
                print(f"{rule['name']} | 매월 {rule['day']}일 | {rule['type']} | {rule['category']} | {rule['amount']}")
        else:
            print(f'[완료] generated={service.generate(args.month)}')
    return 0
