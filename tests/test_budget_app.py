import contextlib
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch
import zipfile

from budget_app.cli import cell, main
from budget_app.models import Transaction
from budget_app.service import BudgetService


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.service = BudgetService(str(self.root / 'data'))

    def values(self, **changes):
        return dict(dict(date='2024-01-15', type='expense', category='food', amount=15000,
                         memo='점심, 식사', tags=['meal', 'work']), **changes)

    def cli(self, *args, inputs=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out), patch('builtins.input', side_effect=inputs or []):
            code = main(['--data-dir', str(self.service.directory), *args])
        return code, out.getvalue()

    def test_crud_persistence_and_order(self):
        first = self.service.add(self.values(date='2024-02-01'))
        second = self.service.add(self.values())
        third = self.service.add(self.values(date='2024-02-01'))
        reopened = BudgetService(str(self.service.directory))
        self.assertEqual([r['id'] for r in reopened.ordered()], [third.id, first.id, second.id])
        self.assertEqual([r['id'] for r in reopened.ordered(limit=1)], [third.id])
        reopened.update(second.id, {'amount': '100', 'memo': '', 'tags': ''})
        row = next(reopened.filtered(end='2024-01-31'))
        self.assertEqual((row['amount'], row['memo'], row['tags']), (100, '', []))
        reopened.transactions.change(first.id, None)
        self.assertEqual(len(list(reopened.filtered())), 2)

    def test_validation_and_missing_ids(self):
        for changes in [dict(date='2024-02-30'), dict(date='2024-1-01'), dict(amount=0),
                        dict(amount=-1), dict(amount='1.5'), dict(type='other'), dict(category='missing')]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.service.add(self.values(**changes))
        for action in [lambda: self.service.update('missing', {'memo': 'x'}),
                       lambda: self.service.transactions.change('missing', None)]:
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(self.service.transactions.path.read_text(), '')

    def test_search_summary_and_budget(self):
        self.service.add(self.values())
        self.service.add(self.values(category='rent', amount=30000, tags=[]))
        self.service.add(self.values(type='income', category='salary', amount=100000))
        rows = list(self.service.ordered(start='2024-01-15', end='2024-01-15', category='food', type='expense', q='점심', tag='meal'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(list(self.service.filtered(tag='unknown')), [])
        self.service.set_budget('2024-01', 20000)
        self.service.set_budget('2024-01', 40000)
        summary = BudgetService(str(self.service.directory)).summary('2024-01', 1)
        self.assertEqual((summary['income'], summary['expense'], summary['balance']), (100000, 45000, 55000))
        self.assertEqual(summary['top'], [('rent', 30000)])
        self.assertEqual(summary['budget'], 40000)
        code, output = self.cli('summary', '--month', '2024-01')
        self.assertEqual(code, 0)
        self.assertIn('112.5%', output)
        self.assertIn('예산 초과', output)
        self.assertIn('데이터 없음', self.cli('summary', '--month', '2025-01')[1])
        for kwargs in [dict(start='2024-02-01', end='2024-01-01'), dict(month='2024-13'), dict(category='missing')]:
            with self.assertRaises(ValueError):
                list(self.service.filtered(**kwargs))

    def test_categories(self):
        self.service.category_change('한글')
        self.assertIn('한글', BudgetService(str(self.service.directory)).category_names())
        with self.assertRaises(ValueError):
            self.service.category_change('한글')
        self.service.category_change('한글', remove=True)
        self.service.add(self.values())
        with self.assertRaises(ValueError):
            self.service.category_change('food', remove=True)

    def test_csv_round_trip_invalid_rows_and_export_protection(self):
        self.service.add(self.values())
        path = self.root / 'out.csv'
        self.assertEqual(self.service.export_csv(str(path), month='2024-01'), 1)
        other = BudgetService(str(self.root / 'other'))
        self.assertEqual(other.import_csv(str(path)), (1, 0))
        original = next(self.service.filtered())
        imported = next(other.filtered())
        self.assertNotEqual(original.pop('id'), imported.pop('id'))
        self.assertEqual(original, imported)
        path.write_text('date,type,category,amount\n2024-01-01,expense,food,1\n2024-13-01,expense,food,2\n', encoding='utf-8')
        code, output = self.cli('import', '--from', str(path))
        self.assertEqual(code, 1)
        self.assertIn('imported=1, skipped=1', output)
        self.assertIn('3행', output)
        for filters in [{}, dict(month='2024-01', start='2024-01-01'), dict(start='bad')]:
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                self.service.export_csv(str(path), **filters)
            self.assertEqual(path.read_bytes(), before)
        with self.assertRaises(ValueError):
            self.service.export_csv(str(self.service.transactions.path), month='2024-01')
        self.assertEqual(self.service.export_csv(str(path), start='2025-01-01'), 0)
        self.assertEqual(path.read_text().strip(), 'date,type,category,amount,memo,tags')
        path.write_text('wrong,header\n1,2\n')
        with self.assertRaises(ValueError):
            self.service.import_csv(str(path))

    def test_atomic_failure_preserves_original(self):
        transaction = self.service.add(self.values())
        before = self.service.transactions.path.read_bytes()
        with patch('budget_app.storage.os.replace', side_effect=OSError('disk error')):
            with self.assertRaises(OSError):
                self.service.update(transaction.id, {'amount': 1})
        self.assertEqual(self.service.transactions.path.read_bytes(), before)
        self.assertEqual(len(list(self.service.directory.iterdir())), 4)
        with self.assertRaises(ValueError):
            self.service.transactions.change('missing', None)
        self.assertEqual(self.service.transactions.path.read_bytes(), before)

    def test_corruption_and_file_failure_cli(self):
        self.service.transactions.path.write_text('{bad}\n')
        code, output = self.cli('list')
        self.assertEqual(code, 1)
        self.assertIn('손상된', output)
        self.assertNotIn('Traceback', output)
        code, output = self.cli('import', '--from', str(self.root / 'missing.csv'))
        self.assertEqual(code, 1)
        self.assertIn('[힌트]', output)
        self.assertNotIn('Traceback', output)

    def test_cli_interactive_and_mutations(self):
        code, output = self.cli('add', inputs=['2024-01-01', 'expense', 'food', '50', '밥', 'meal'])
        self.assertEqual(code, 0)
        self.assertIn('id=TX-', output)
        identifier = next(self.service.filtered())['id']
        self.assertEqual(self.cli('update', '--id', identifier, '--amount', '20')[0], 0)
        self.assertEqual(self.cli('update', '--id', identifier)[0], 1)
        self.assertEqual(self.cli('search', '--tag', 'meal')[0], 0)
        self.assertEqual(self.cli('budget', 'set', '--month', '2024-01', '--amount', '100')[0], 0)
        self.assertEqual(self.cli('category', 'add', inputs=['travel'])[0], 0)
        self.assertIn('travel', self.cli('category', 'list')[1])
        self.assertEqual(self.cli('category', 'remove', inputs=['travel'])[0], 0)
        self.assertEqual(self.cli('delete', '--id', identifier)[0], 0)
        self.assertEqual(self.cli('delete', '--id', identifier)[0], 1)
        self.assertEqual(self.cli('add', inputs=['bad', 'expense', 'food', '1', '', ''])[0], 1)

    def test_help_and_parser_exit_codes(self):
        commands = [[], ['add'], ['list'], ['search'], ['summary'], ['update'], ['delete'], ['import'], ['export'],
                    ['budget'], ['budget', 'set'], ['category'], ['category', 'add'], ['category', 'list'],
                    ['category', 'remove'], ['backup'], ['recurring'], ['recurring', 'add'],
                    ['recurring', 'list'], ['recurring', 'generate']]
        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run([sys.executable, '-m', 'budget_app', *command, '--help'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('usage:', result.stdout)
        result = subprocess.run([sys.executable, '-m', 'budget_app', 'list', '--limit', '0'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('[힌트]', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_backup_recurring_and_formatting(self):
        self.service.add_rule('rent', 31, self.values())
        self.assertEqual(self.service.generate('2024-02'), 1)
        self.assertEqual(BudgetService(str(self.service.directory)).generate('2024-02'), 0)
        self.assertEqual(next(self.service.filtered())['date'], '2024-02-29')
        self.assertEqual(self.service.generate('2024-03'), 1)
        with self.assertRaises(ValueError):
            self.service.category_change('food', remove=True)
        target = self.service.backup()
        with zipfile.ZipFile(target) as archive:
            self.assertEqual(set(archive.namelist()), {'transactions.jsonl', 'categories.jsonl', 'budgets.jsonl', 'recurring.jsonl'})
            self.assertEqual(archive.read('transactions.jsonl'), self.service.transactions.path.read_bytes())
        self.assertEqual(cell('한글abcdef', 6), '한글ab')
        self.assertEqual(cell('한', 4), '한  ')
        self.assertNotIn('\n', cell('a\nb', 5))

    def test_commands_across_processes(self):
        def run(*args, data_dir=None, input_text=None):
            return subprocess.run(
                [sys.executable, '-m', 'budget_app', '--data-dir',
                 str(data_dir or self.service.directory), *args],
                input=input_text, capture_output=True, text=True)

        result = run('add', input_text='2024-01-15\nexpense\nfood\n15000\n점심\nmeal\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('15000', run('list').stdout)
        path = self.root / 'process.csv'
        result = run('export', '--out', str(path), '--month', '2024-01')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('1 records', result.stdout)
        result = run('import', '--from', str(path), data_dir=self.root / 'restored')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('15000', run('list', data_dir=self.root / 'restored').stdout)
        result = run('recurring', 'add', input_text='월세\n31\nexpense\nrent\n500000\n\n\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('월세', run('recurring', 'list').stdout)
        self.assertIn('generated=1', run('recurring', 'generate', '--month', '2024-02').stdout)
        self.assertIn('generated=0', run('recurring', 'generate', '--month', '2024-02').stdout)
        result = run('backup')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(list(self.service.directory.glob('backup-*.zip')))

    def test_large_ordered_query_bounded_python_memory(self):
        base = self.values(memo='x' * 500)
        self.service.transactions.replace(dict(base, id=f'TX-{i}', date=f'2024-01-{i % 28 + 1:02}') for i in range(12000))
        tracemalloc.start()
        count = 0
        previous = '9999-12-31'
        try:
            for record in self.service.ordered():
                self.assertLessEqual(record['date'], previous)
                previous = record['date']
                count += 1
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(count, 12000)
        self.assertLess(peak, 4 * 1024 * 1024)


if __name__ == '__main__':
    unittest.main()
