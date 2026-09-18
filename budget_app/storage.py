"""Streaming JSONL storage with atomic replacement."""
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any
import json
import os
import tempfile


class JsonStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    def records(self) -> Iterator[dict[str, Any]]:
        with self.path.open(encoding='utf-8') as stream:
            for number, line in enumerate(stream, 1):
                try:
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError('객체가 아닙니다')
                    yield value
                except (ValueError, TypeError) as error:
                    raise ValueError(f'{self.path}:{number} 손상된 JSONL. 백업을 복구하세요: {error}') from error

    def replace(self, records: Iterable[dict[str, Any]]) -> None:
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent,
                                             delete=False) as stream:
                name = stream.name
                for record in records:
                    stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)


class TransactionRepository(JsonStore):
    def add(self, records: Iterable[dict[str, Any]]) -> None:
        def combined() -> Iterator[dict[str, Any]]:
            yield from self.records()
            yield from records
        self.replace(combined())

    def change(self, identifier: str, replacement: dict[str, Any] | None) -> None:
        def changed() -> Iterator[dict[str, Any]]:
            found = False
            for record in self.records():
                if record['id'] == identifier:
                    found = True
                    if replacement is not None:
                        yield replacement
                else:
                    yield record
            if not found:
                raise ValueError('없는 데이터입니다. list에서 ID를 확인하세요.')
        self.replace(changed())
