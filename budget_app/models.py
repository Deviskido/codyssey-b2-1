"""Typed records and shared validation."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any
import re
import uuid


def date_value(value: str) -> str:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('날짜 형식 오류. YYYY-MM-DD로 입력하세요.')
    datetime.strptime(value, '%Y-%m-%d')
    return value


def month_value(value: str) -> str:
    date_value(value + '-01')
    return value


def positive(value: Any) -> int:
    if isinstance(value, bool) or not re.fullmatch(r'[0-9]+', str(value)) or int(value) <= 0:
        raise ValueError('금액/개수는 양수 정수로 입력하세요.')
    return int(value)


@dataclass
class Transaction:
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ''
    tags: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, values: dict[str, Any], categories: list[str]) -> 'Transaction':
        data = dict(values)
        data.setdefault('id', 'TX-' + uuid.uuid4().hex)
        data['date'] = date_value(data['date'])
        data['amount'] = positive(data['amount'])
        if data['type'] not in ('income', 'expense'):
            raise ValueError('type은 income 또는 expense로 입력하세요.')
        if data['category'] not in categories:
            raise ValueError('등록되지 않은 category입니다. category add로 등록하세요.')
        if not isinstance(data['id'], str) or not data['id']:
            raise ValueError('거래 ID가 올바르지 않습니다.')
        tags = data.get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
            raise ValueError('tags는 문자열 목록이어야 합니다.')
        data['tags'] = tags
        if not isinstance(data.get('memo', ''), str):
            raise ValueError('memo는 문자열이어야 합니다.')
        return cls(**data)

    def record(self) -> dict[str, Any]:
        return asdict(self)
