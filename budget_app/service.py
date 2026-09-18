"""Ledger operations; SQLite is a temporary disk-backed sorting workspace only."""
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any
import calendar
import csv
import json
import sqlite3
import tempfile
import zipfile
from datetime import datetime

from .models import Transaction, date_value, month_value, positive
from .storage import JsonStore, TransactionRepository

FIELDS = ['date', 'type', 'category', 'amount', 'memo', 'tags']


class BudgetService:
    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.transactions = TransactionRepository(self.directory / 'transactions.jsonl')
        self.categories = JsonStore(self.directory / 'categories.jsonl')
        self.budgets = JsonStore(self.directory / 'budgets.jsonl')
        self.rules = JsonStore(self.directory / 'recurring.jsonl')
        if not self.category_names():
            self.categories.replace({'name': name} for name in ['food', 'transport', 'rent', 'salary', 'etc'])

    def category_names(self) -> list[str]:
        return [r['name'] for r in self.categories.records()]

    def category_change(self, name: str, remove: bool = False) -> None:
        names = self.category_names()
        if not name.strip():
            raise ValueError('카테고리명을 입력하세요.')
        if remove:
            if name not in names:
                raise ValueError('없는 카테고리입니다. category list를 확인하세요.')
            if any(t['category'] == name for t in self.transactions.records()) or any(r['category'] == name for r in self.rules.records()):
                raise ValueError('사용 중인 카테고리는 삭제할 수 없습니다.')
            names.remove(name)
        else:
            if name in names:
                raise ValueError('중복 카테고리입니다. 다른 이름을 입력하세요.')
            names.append(name)
        self.categories.replace({'name': n} for n in names)

    def add(self, values: dict[str, Any]) -> Transaction:
        transaction = Transaction.create(values, self.category_names())
        self.transactions.add([transaction.record()])
        return transaction

    def update(self, identifier: str, values: dict[str, Any]) -> None:
        for record in self.transactions.records():
            if record['id'] == identifier:
                record.update(values)
                replacement = Transaction.create(record, self.category_names()).record()
                self.transactions.change(identifier, replacement)
                return
        raise ValueError('없는 데이터입니다. list에서 ID를 확인하세요.')

    def filtered(self, **filters: Any) -> Iterator[dict[str, Any]]:
        start, end, month = filters.get('start'), filters.get('end'), filters.get('month')
        if start:
            date_value(start)
        if end:
            date_value(end)
        if start and end and start > end:
            raise ValueError('--from은 --to보다 늦을 수 없습니다.')
        if month:
            month_value(month)
        categories = self.category_names()
        if filters.get('category') and filters['category'] not in categories:
            raise ValueError('없는 카테고리입니다. category list를 확인하세요.')
        for raw in self.transactions.records():
            r = Transaction.create(raw, categories).record()
            if start and r['date'] < start or end and r['date'] > end:
                continue
            if month and not r['date'].startswith(month + '-'):
                continue
            if any(filters.get(k) and r[k] != filters[k] for k in ('category', 'type')):
                continue
            if filters.get('q') and filters['q'] not in r['memo']:
                continue
            if filters.get('tag') and filters['tag'] not in r['tags']:
                continue
            yield r

    def ordered(self, limit: int | None = None, **filters: Any) -> Iterator[dict[str, Any]]:
        # Bounded SQLite page cache and file-backed temporary sorting avoid a full Python list.
        with tempfile.TemporaryDirectory() as directory:
            db = sqlite3.connect(str(Path(directory) / 'sort.sqlite'))
            try:
                db.execute('PRAGMA cache_size=-1024')
                db.execute('PRAGMA temp_store=FILE')
                db.execute('CREATE TABLE records (seq INTEGER PRIMARY KEY, date TEXT, body TEXT)')
                db.executemany('INSERT INTO records(date, body) VALUES (?, ?)',
                               ((r['date'], json.dumps(r)) for r in self.filtered(**filters)))
                query = 'SELECT body FROM records ORDER BY date DESC, seq DESC'
                params = ()
                if limit is not None:
                    query += ' LIMIT ?'
                    params = (positive(limit),)
                for (body,) in db.execute(query, params):
                    yield json.loads(body)
            finally:
                db.close()

    def summary(self, month: str, top: int) -> dict[str, Any]:
        month_value(month)
        positive(top)
        income = expense = count = 0
        totals: dict[str, int] = defaultdict(int)
        for r in self.filtered(month=month):
            count += 1
            if r['type'] == 'income':
                income += r['amount']
            else:
                expense += r['amount']
                totals[r['category']] += r['amount']
        budget = next((positive(r['amount']) for r in self.budgets.records() if r['month'] == month), None)
        return dict(income=income, expense=expense, balance=income-expense, count=count,
                    top=sorted(totals.items(), key=lambda pair: (-pair[1], pair[0]))[:top], budget=budget)

    def set_budget(self, month: str, amount: int) -> None:
        month_value(month)
        amount = positive(amount)
        def records() -> Iterator[dict[str, Any]]:
            yield from (r for r in self.budgets.records() if r['month'] != month)
            yield {'month': month, 'amount': amount}
        self.budgets.replace(records())

    def import_csv(self, path: str) -> tuple[int, int]:
        imported = skipped = 0
        categories = self.category_names()
        with open(path, encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            if not set(FIELDS[:4]).issubset(reader.fieldnames or []):
                raise ValueError('CSV 필수 헤더: date,type,category,amount를 확인하세요.')
            def records() -> Iterator[dict[str, Any]]:
                nonlocal imported, skipped
                for row in reader:
                    try:
                        if None in row:
                            raise ValueError('열 개수 오류. 쉼표가 있는 값은 따옴표로 감싸세요.')
                        values = {k: row.get(k, '') for k in FIELDS}
                        record = Transaction.create(values, categories).record()
                    except (ValueError, TypeError, KeyError) as error:
                        skipped += 1
                        print(f'[오류] CSV {reader.line_num}행: {error} [힌트] 행을 수정 후 다시 가져오세요.')
                        continue
                    imported += 1
                    yield record
            self.transactions.add(records())
        return imported, skipped

    def export_csv(self, path: str, **filters: Any) -> int:
        if not any(filters.get(k) for k in ('month', 'start', 'end')):
            raise ValueError('--month 또는 --from/--to 조건을 입력하세요.')
        if filters.get('month') and (filters.get('start') or filters.get('end')):
            raise ValueError('월과 기간 조건 중 하나만 사용하세요.')
        destination = Path(path).resolve()
        if destination in [s.path.resolve() for s in (self.transactions, self.categories, self.budgets, self.rules)]:
            raise ValueError('저장 파일을 덮어쓸 수 없습니다. 다른 CSV 경로를 입력하세요.')
        count = 0
        name = None
        import os
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=destination.parent, delete=False) as stream:
                name = stream.name
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                for r in self.ordered(**filters):
                    writer.writerow({k: ','.join(r[k]) if k == 'tags' else r[k] for k in FIELDS})
                    count += 1
            os.replace(name, destination)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
        return count

    def backup(self) -> Path:
        target = self.directory / ('backup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.zip')
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            for store in (self.transactions, self.categories, self.budgets, self.rules):
                archive.write(store.path, store.path.name)
        return target

    def add_rule(self, name: str, day: int, values: dict[str, Any]) -> None:
        if not name.strip() or any(r['name'] == name for r in self.rules.records()):
            raise ValueError('비어 있지 않은 고유 규칙명을 입력하세요.')
        if not 1 <= day <= 31:
            raise ValueError('day는 1~31로 입력하세요.')
        record = Transaction.create(dict(values, date=f'2000-01-{day:02d}'), self.category_names()).record()
        record.update(name=name, day=day)
        self.rules.replace(iter([*self.rules.records(), record]))

    def generate(self, month: str) -> int:
        month_value(month)
        year, number = map(int, month.split('-'))
        existing = {r['id'] for r in self.transactions.records()}
        count = 0
        def records() -> Iterator[dict[str, Any]]:
            nonlocal count
            for rule in self.rules.records():
                identifier = f"{rule['id']}-{month}"
                if identifier in existing:
                    continue
                day = min(rule['day'], calendar.monthrange(year, number)[1])
                record = {k: rule[k] for k in FIELDS if k != 'date'}
                record.update(id=identifier, date=f'{month}-{day:02d}')
                yield Transaction.create(record, self.category_names()).record()
                count += 1
        self.transactions.add(records())
        return count
